# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import base64
import binascii
import collections
import email
import email.message
import email.policy
import email.utils
import hashlib
import ipaddress
import logging
import os.path
import re
import typing
import uuid
import warnings
from collections import Counter

import dateutil.parser
from tld import get_fld
from urlextract import URLExtract

from . import EmailParserDecode, EmailParserRegex, EmailParserRouting

logger = logging.getLogger(__name__)

try:
    import magic
except ImportError:
    magic = None
else:
    if not hasattr(magic, "open"):
        logger.warning(
            "You are using python-magic, though this module requires file-magic. Disabling magic usage due to incompatibilities.",
        )

        magic = None


class EmlParser:
    def __init__(
        self,
        include_raw_body: bool = False,
        include_attachment_data: bool = False,
        pconf: dict | None = None,
        policy: email.policy.Policy = email.policy.default,
        ignore_bad_start: bool = False,
        email_force_tld: bool = False,
        parse_attachments: bool = True,
    ) -> None:
        self.include_raw_body = include_raw_body
        self.include_attachment_data = include_attachment_data
        # If no pconf was specified, default to empty dict
        self.pconf = pconf or {}
        self.policy = policy
        self.ignore_bad_start = ignore_bad_start
        self.email_force_tld = email_force_tld
        self.parse_attachments = parse_attachments

        if self.email_force_tld:
            EmailParserRegex.email_regex = EmailParserRegex.email_force_tld_regex

        # If no allowlisting is required, set to emtpy list
        if "whiteip" not in self.pconf:
            self.pconf["whiteip"] = []
        # If no allowlisting is required, set to emtpy list
        if "whitefor" not in self.pconf:
            self.pconf["whitefor"] = []

        self.msg: email.message.Message | None = None

    def decode_email(
        self,
        eml_file: os.PathLike[str],
        ignore_bad_start: bool = False,
    ) -> dict:
        """Function for decoding an EML file into an easily parsable structure.

        Some intelligence is applied while parsing the file in order to work around
        broken files.
        Besides just parsing, this function also computes hashes and extracts meta
        information from the source file.

        Args:
            eml_file: Path to the file to be parsed. os.PathLike objects are supported.
            ignore_bad_start: Ignore invalid file start for this run. This has a considerable performance impact.

        Returns:
            dict: A dictionary with the content of the EML parsed and broken down into
                  key-value pairs.

        """
        with open(eml_file, "rb") as fp:
            raw_email = fp.read()

        return self.decode_email_bytes(raw_email, ignore_bad_start=ignore_bad_start)

    def decode_email_bytes(
        self,
        eml_file: bytes,
        ignore_bad_start: bool = False,
    ) -> dict:
        """Function for decoding an EML file into an easily parsable structure.

        Some intelligence is applied while parsing the file in order to work around
        broken files.
        Besides just parsing, this function also computes hashes and extracts meta
        information from the source file.

        Args:
            eml_file: Contents of the raw EML file passed to this function as string.
            ignore_bad_start: Ignore invalid file start for this run. This has a considerable performance impact.

        Returns:
            dict: A dictionary with the content of the EML parsed and broken down into
                  key-value pairs.

        """
        if self.ignore_bad_start or ignore_bad_start:
            # Skip invalid start of file
            # Note that this has a considerable performance impact, which is why it is disabled by default.
            _eml_file = b""

            if b":" not in eml_file.split(b"\n", 1):
                start = True
                for line in eml_file.split(b"\n"):
                    if start and b":" not in line:
                        continue

                    start = False

                    _eml_file += line
            else:
                _eml_file = eml_file
        else:
            _eml_file = eml_file

        self.msg = email.message_from_bytes(_eml_file, policy=self.policy)

        return self.parse_email()

    def parse_routing(self, entries) -> dict:
        r = {}
        r["hosts"] = []
        r["ips"] = []
        r["domains"] = []

        for entry in entries:
            try:
                ip_obj = ipaddress.ip_address(entry)
            except ValueError:
                logger.debug(f'Invalid IP in received line - "{entry}"')
                try:
                    dom = get_fld(entry.lower(), fix_protocol=True)
                    r["domains"].append(dom)
                    r["hosts"].append(entry)
                except Exception:
                    r["hosts"].append(entry)
            else:
                if not (ip_obj.is_private):
                    r["ips"].append(str(ip_obj))
        return r

    def parse_email(self) -> dict:
        """Parse an e-mail and return a dictionary containing the various parts of\
        the e-mail broken down into key-value pairs.

        Args:
          msg (str): Raw EML e-mail string.
          include_raw_body (bool, optional): If True, includes the raw body in the resulting
                                   dictionary. Defaults to False.
          include_attachment_data (bool, optional): If True, includes the full attachment
                                                    data in the resulting dictionary.
                                                    Defaults to False.
          pconf (dict, optional): A dict with various optional configuration parameters,
                                  e.g. allowlist IPs, allowlist e-mail addresses, etc.

          parse_attachments (bool, optional): Set this to false if you want to disable the parsing of attachments.
                                              Please note that HTML attachments as well as other text data marked to be
                                              in-lined, will always be parsed.

        Returns:
          dict: A dictionary with the content of the EML parsed and broken down into
                key-value pairs.

        """
        header: dict[str, typing.Any] = {}
        report_struc: dict[str, typing.Any] = {}  # Final structure
        headers_struc: dict[str, typing.Any] = {}  # header_structure
        bodys_struc: dict[str, typing.Any] = {}  # body structure

        if self.msg is None:
            raise ValueError("msg is not set.")

        # parse and decode subject
        subject = self.msg.get("subject", "")
        headers_struc["subject"] = EmailParserDecode.decode_field(subject)

        # If parsing had problems, report it
        if self.msg.defects:
            headers_struc["defect"] = []
            for exception in self.msg.defects:
                headers_struc["defect"].append(str(exception))

        try:
            msg_header_field = str(self.msg.get("from", "")).lower()
        except (IndexError, AttributeError):
            _from = EmailParserDecode.workaround_bug_27257(self.msg, "from")
            self.msg.__delitem__("from")

            if _from:
                self.msg.add_header("from", _from[0])
                __from = _from[0].lower()
            else:
                self.msg.add_header("from", "")
                __from = ""

            msg_header_field = __from

        if msg_header_field != "":
            m = EmailParserRegex.email_regex.search(msg_header_field)
            if m:
                headers_struc["from"] = m.group(1)
            else:
                from_ = email.utils.parseaddr(self.msg.get("from", "").lower())
                headers_struc["from"] = from_[1]

        # parse and decode "to"
        headers_struc["to"] = self.headeremail2list("to")
        # parse and decode "cc"
        headers_struc["cc"] = self.headeremail2list("cc")
        if not headers_struc["cc"]:
            headers_struc.pop("cc")

        # parse and decode delivered-to
        headers_struc["delivered_to"] = self.headeremail2list("delivered-to")
        if not headers_struc["delivered_to"]:
            headers_struc.pop("delivered_to")

        # parse and decode Date
        # If date field is present
        if "date" in self.msg:
            try:
                msg_date = self.msg.get("date")
            except TypeError:
                logger.warning("Error parsing date.", exc_info=True)
                headers_struc["date"] = dateutil.parser.parse(
                    "1970-01-01T00:00:00+0000",
                )
                self.msg.replace_header("date", headers_struc["date"])
            else:
                headers_struc["date"] = EmailParserDecode.robust_string2date(msg_date)

        else:
            # If date field is absent...
            headers_struc["date"] = dateutil.parser.parse("1970-01-01T00:00:00+0000")

        # mail receiver path / parse any domain, e-mail
        # @TODO parse case where domain is specified but in parentheses only an IP
        headers_struc["received"] = []
        headers_struc["received_email"] = []
        headers_struc["received_domain"] = []
        headers_struc["received_ip"] = []
        headers_struc["received_domains_internal"] = []
        headers_struc["sending"] = []
        headers_struc["receiving"] = []

        try:
            found_smtpin: collections.Counter = (
                collections.Counter()
            )  # Array for storing potential duplicate "HOP"

            for received_line in self.msg.get_all("received", []):
                line = str(received_line).lower()

                received_line_flat = re.sub(
                    r"(\r|\n|\s|\t)+",
                    " ",
                    line,
                    flags=re.UNICODE,
                )

                # Parse and split routing headers.
                # Return dict of list
                #   date string
                #   from list
                #   for list
                #   by list
                #   with string
                #   warning list

                parsed_routing = EmailParserRouting.parserouting(received_line_flat)
                sending = {}
                sending["ips"] = []
                sending["domains"] = []
                sending["emails"] = []
                sending["hosts"] = []

                receiving = {}
                receiving["ips"] = []
                receiving["domains"] = []
                receiving["emails"] = []
                receiving["hosts"] = []
                from_routing = self.parse_routing(parsed_routing.get("from", []))
                sending["ips"].extend(from_routing["ips"])
                sending["domains"].extend(from_routing["domains"])
                sending["hosts"].extend(from_routing["hosts"])
                # print(sending)
                to_routing = self.parse_routing(parsed_routing.get("by", []))
                receiving["ips"].extend(to_routing["ips"])
                receiving["domains"].extend(to_routing["domains"])
                receiving["hosts"].extend(to_routing["hosts"])
                print(receiving)

                if (
                    len(receiving["ips"]) > 0
                    or len(receiving["domains"]) > 0
                    or len(receiving["hosts"]) > 0
                ):
                    headers_struc["receiving"].append(receiving)

                if (
                    len(sending["ips"]) > 0
                    or len(sending["domains"]) > 0
                    or len(sending["hosts"]) > 0
                ):
                    headers_struc["sending"].append(sending)

                # If required collect the IP of the gateway that have injected the mail.
                # Iterate all parsed item and find IP
                # It is parsed from the MOST recent to the OLDEST (from IN > Out)
                # We match external IP from the most "OUT" Found.
                # Warning .. It may be spoofed !!
                # It add a warning if multiple identical items are found.

                if self.pconf.get("byhostentry"):
                    for by_item in parsed_routing.get("by", []):
                        for byhostentry_ in self.pconf["byhostentry"]:
                            byhostentry = byhostentry_.lower()
                            print(f"{byhostentry} {by_item}")
                            if byhostentry in by_item:
                                # Save the last Found.. ( most external )
                                headers_struc["received_src"] = parsed_routing.get(
                                    "from",
                                )

                                # Increment watched by detection counter, and warn if needed
                                found_smtpin[byhostentry] += 1
                                if (
                                    found_smtpin[byhostentry] > 1
                                ):  # Twice found the header...
                                    if parsed_routing.get("warning"):
                                        parsed_routing["warning"].append(
                                            ["Duplicate SMTP by entrypoint"],
                                        )
                                    else:
                                        parsed_routing["warning"] = [
                                            "Duplicate SMTP by entrypoint",
                                        ]

                headers_struc["received"].append(parsed_routing)

                # Parse IPs in "received headers"
                ips_in_received_line = EmailParserRegex.ipv6_regex.findall(
                    received_line_flat,
                ) + EmailParserRegex.ipv4_regex.findall(received_line_flat)
                for ip in ips_in_received_line:
                    try:
                        ip_obj = ipaddress.ip_address(
                            ip,
                        )  # type of findall is list[str], so this is correct
                    except ValueError:
                        logger.debug(f'Invalid IP in received line - "{ip}"')
                    else:
                        if not (
                            ip_obj.is_private or str(ip_obj) in self.pconf["whiteip"]
                        ):
                            headers_struc["received_ip"].append(str(ip_obj))

                # search for domain

                for m in EmailParserRegex.recv_dom_regex.findall(received_line_flat):
                    try:
                        ip_obj = ipaddress.ip_address(
                            m,
                        )  # type of findall is list[str], so this is correct
                    except ValueError:
                        # we find IPs using the previous IP crawler, hence we ignore them
                        # here.
                        # iff the regex fails, we add the entry
                        try:
                            dom = get_fld(m.lower(), fix_protocol=True)
                            headers_struc["received_domain"].append(dom)
                        except:
                            headers_struc["received_domains_internal"].append(m.lower())

                # search for e-mail addresses
                for mail_candidate in EmailParserRegex.email_regex.findall(
                    received_line_flat,
                ):
                    if mail_candidate not in parsed_routing.get("for", []):
                        headers_struc["received_email"] += [mail_candidate]

        except TypeError:  # Ready to parse email without received headers.
            logger.exception("Exception occurred while parsing received lines.")

        # Concatenate for emails into one array | uniq
        # for rapid "find"

        headers_struc["received_foremail"] = []
        if "received" in headers_struc:
            for _parsed_routing in headers_struc["received"]:
                # print(_parsed_routing)
                for itemfor in _parsed_routing.get("for", []):
                    if itemfor not in self.pconf["whitefor"]:
                        headers_struc["received_foremail"].append(itemfor)

        # Uniq data found
        headers_struc["received_email"] = list(set(headers_struc["received_email"]))
        headers_struc["received_domain"] = list(set(headers_struc["received_domain"]))
        headers_struc["received_ip"] = list(set(headers_struc["received_ip"]))
        headers_struc["received_domains_internal"] = list(
            set(headers_struc["received_domains_internal"]),
        )

        # Clean up if empty
        if not headers_struc["received_email"]:
            del headers_struc["received_email"]

        if "received_foremail" in headers_struc:
            if not headers_struc["received_foremail"]:
                del headers_struc["received_foremail"]
            else:
                headers_struc["received_foremail"] = list(
                    set(headers_struc["received_foremail"]),
                )

        if not headers_struc["received_domain"]:
            del headers_struc["received_domain"]

        if not headers_struc["received_ip"]:
            del headers_struc["received_ip"]
        ####################

        # Parse text body
        raw_body = self.get_raw_body_text(self.msg)

        if self.include_raw_body:
            bodys_struc["raw_body"] = raw_body

        bodys = {}

        # Is it a multipart email ?
        if len(raw_body) == 1:
            multipart = False
        else:
            multipart = True

        for body_tup in raw_body:
            bodie: dict[str, typing.Any] = {}
            _, body, body_multhead = body_tup
            # Parse any URLs and mail found in the body
            list_observed_urls: list[str] = []
            list_observed_email: typing.Counter[str] = Counter()
            list_observed_dom: typing.Counter[str] = Counter()
            list_observed_ip: typing.Counter[str] = Counter()

            # If we start directly a findall on 500K+ body we got time and memory issues...
            # if more than 4K.. lets cheat, we will cut around the thing we search "://, @, ."
            # in order to reduce regex complexity.
            for body_slice in self.string_sliding_window_loop(body):
                list_observed_urls = self.get_uri_ondata(body_slice)
                extractor = URLExtract(extract_email=True)

                for match in extractor.find_urls(body_slice):
                    # for match in EmailParserRegex.email_regex.findall(body_slice):
                    c = URLExtract()
                    removedurl = c.find_urls(match)
                    if not removedurl:
                        match = match.replace("mailto:", "")
                        list_observed_email[match.lower()] = 1

                # for match in EmailParserRegex.dom_regex.findall(body_slice):
                for match in list_observed_urls:
                    try:
                        dom = get_fld(match.lower(), fix_protocol=True)
                        list_observed_dom[dom] = 1
                    except Exception:
                        pass
                for match in EmailParserRegex.ipv4_regex.findall(body_slice):
                    try:
                        ipaddress_match = ipaddress.ip_address(match)
                    except ValueError:
                        continue
                    else:
                        if not (
                            ipaddress_match.is_private or match in self.pconf["whiteip"]
                        ):
                            list_observed_ip[match] = 1
                for match in EmailParserRegex.ipv6_regex.findall(body_slice):
                    try:
                        ipaddress_match = ipaddress.ip_address(match)
                    except ValueError:
                        continue
                    else:
                        if not (
                            ipaddress_match.is_private or match in self.pconf["whiteip"]
                        ):
                            list_observed_ip[match] = 1

            # Report uri,email and observed domain or hash if no raw body
            if self.include_raw_body:
                if list_observed_urls:
                    bodie["uri"] = list(list_observed_urls)

                if list_observed_email:
                    bodie["email"] = list(list_observed_email)

                if list_observed_dom:
                    bodie["domain"] = list(list_observed_dom)

                if list_observed_ip:
                    bodie["ip"] = list(list_observed_ip)

            else:
                if list_observed_urls:
                    bodie["uri_hash"] = []
                    for element in list_observed_urls:
                        bodie["uri_hash"].append(self.wrap_hash_sha256(element.lower()))
                if list_observed_email:
                    bodie["email_hash"] = []
                    for element in list_observed_email:
                        # Email already lowered
                        bodie["email_hash"].append(self.wrap_hash_sha256(element))
                if list_observed_dom:
                    bodie["domain_hash"] = []
                    # for uri in list(set(list_observed_dom)):
                    for element in list_observed_dom:
                        bodie["domain_hash"].append(self.wrap_hash_sha256(element))
                if list_observed_ip:
                    bodie["ip_hash"] = []
                    for element in list_observed_ip:
                        # IP (v6) already lowered
                        bodie["ip_hash"].append(self.wrap_hash_sha256(element))

            # For mail without multipart we will only get the "content....something" headers
            # all other headers are in "header"
            # but we need to convert header tuples in dict..
            # "a","toto"           a: [toto,titi]
            # "a","titi"   --->    c: [truc]
            # "c","truc"
            ch: dict[str, list] = {}
            for k, v in body_multhead:
                # make sure we are working with strings only
                v = str(v)

                # We are using replace . to : for avoiding issue in mongo
                k = k.lower().replace(".", ":")  # Lot of lowers, pre-compute :) .
                # print v
                if multipart or k.startswith("content"):
                    if k in ch:
                        ch[k].append(v)
                    else:
                        ch[k] = [v]
            bodie["content_header"] = ch  # Store content headers dict

            if self.include_raw_body:
                bodie["content"] = body

            # Sometimes bad people play with multiple header instances.
            # We "display" the "LAST" one .. as does thunderbird
            val = ch.get("content-type")
            if val:
                header_val = val[-1]
                bodie["content_type"] = header_val.split(";", 1)[0].strip()

            # Hash the body
            bodie["hash"] = hashlib.sha256(body.encode("utf-8")).hexdigest()

            uid = str(uuid.uuid1())
            bodys[uid] = bodie

        bodys_struc = bodys

        # Get all other bulk raw headers
        # "a","toto"           a: [toto,titi]
        # "a","titi"   --->    c: [truc]
        # "c","truc"
        #
        for k in set(self.msg.keys()):
            # We are using replace . to : for avoiding issue in mongo
            k = k.lower()  # Lot of lower, pre-compute...
            decoded_values = []

            try:
                for value in self.msg.get_all(k, []):
                    if value:
                        decoded_values.append(value)
            except (IndexError, AttributeError, TypeError):
                # We have hit a field value parsing error.
                # Try to work around this by using a relaxed policy, if possible.
                # Parsing might not give meaningful results in this case!
                logger.error(
                    "ERROR: Field value parsing error, trying to work around this!",
                )
                decoded_values = (
                    EmailParserDecode.workaround_field_value_parsing_errors(self.msg, k)
                )

            if decoded_values:
                if k in header:
                    header[k] += decoded_values
                else:
                    header[k] = decoded_values

        headers_struc["header"] = header

        # parse attachments
        if self.parse_attachments:
            try:
                report_struc["attachment"] = self.traverse_multipart(self.msg, 0)
            except (binascii.Error, AssertionError):
                # we hit this exception if the payload contains invalid data
                logger.exception(
                    "Exception occurred while parsing attachment data. Collected data will not be complete!",
                )
                report_struc["attachment"] = None

            # Dirty hack... transform hash into list.. need to be done in the function.
            # Mandatory to search efficiently in mongodb
            # See Bug 11 of eml_parser
            if not report_struc["attachment"]:
                del report_struc["attachment"]
            else:
                newattach = []
                for attachment in report_struc["attachment"]:
                    newattach.append(report_struc["attachment"][attachment])
                report_struc["attachment"] = newattach

        newbody = []
        for body in bodys_struc:
            newbody.append(bodys_struc[body])
        report_struc["body"] = newbody
        # End of dirty hack

        # Get all other bulk headers
        report_struc["header"] = headers_struc

        return report_struc

    @staticmethod
    def string_sliding_window_loop(
        body: str,
        slice_step: int = 50000,
    ) -> typing.Iterator[str]:
        """Yield a more or less constant slice of a large string.

        If we start directly a *re* findall on 500K+ body we got time and memory issues.
        If more than the configured slice step, lets cheat, we will cut around the thing we search "://, @, ."
        in order to reduce regex complexity.

        Args:
            body: Body to slice into smaller pieces.
            slice_step: Slice this number or characters.

        Returns:
            typing.Iterator[str]: Sliced body string.

        """
        body_length = len(body)

        if body_length <= slice_step:
            yield body

        else:
            ptr_start = 0

            for ptr_end in range(slice_step, body_length, slice_step):
                if " " in body[ptr_end - 1 : ptr_end]:
                    while not (
                        EmailParserRegex.window_slice_regex.match(
                            body[ptr_end - 1 : ptr_end],
                        )
                        or ptr_end > body_length
                    ):
                        if ptr_end > body_length:
                            ptr_end = body_length
                            break

                        ptr_end += 1

                yield body[ptr_start:ptr_end]

                ptr_start = ptr_end

    @staticmethod
    def get_uri_ondata(body: str) -> list[str]:
        """Function for extracting URLs from the input string.

        Args:
            body (str): Text input which should be searched for URLs.

        Returns:
            list: Returns a list of URLs found in the input string.

        """
        list_observed_urls: typing.Counter[str] = Counter()
        extractor = URLExtract()

        for found_url in extractor.find_urls(body):
            # for found_url in EmailParserRegex.url_regex_simple.findall(body):
            if "." not in found_url:
                # if we found a URL like e.g. http://afafasasfasfas; that makes no
                # sense, thus skip it
                continue
            list_observed_urls[found_url] = 1
            # found_url = urllib.parse.urlparse(found_url).geturl()
            # let's try to be smart by stripping of noisy bogus parts
            # found_url = re.split(r'''[', ")}\\]''', found_url, 1)[0]
            # list_observed_urls[found_url] = 1

        return list(list_observed_urls)

    def headeremail2list(self, header: str) -> list[str]:
        """Parses a given header field with e-mail addresses to a list of e-mail addresses.

        Args:
            header (str): The header field to decode.

        Returns:
            list: Returns a list of strings which represent e-mail addresses.

        """
        if self.msg is None:
            raise ValueError("msg is not set.")

        try:
            field = email.utils.getaddresses(self.msg.get_all(header, []))
        except (IndexError, AttributeError):
            field = email.utils.getaddresses(
                EmailParserDecode.workaround_bug_27257(self.msg, header),
            )

        return_field = []

        for m in field:
            if not m[1] == "":
                if self.email_force_tld:
                    if EmailParserRegex.email_force_tld_regex.match(m[1]):
                        return_field.append(m[1].lower())
                else:
                    return_field.append(m[1].lower())

        return return_field

    # Iterator that give all position of a given pattern (no regex)
    # @FIXME: Is this still required
    # Error may occur when using unicode-literals or python 3 on dirty emails
    # Need to check if buffer is a clean one
    # may be tested with this byte code:
    # -> 00000b70  61 6c 20 32 39 b0 20 6c  75 67 6c 69 6f 20 32 30  |al 29. luglio 20|
    # Should crash on "B0".
    @staticmethod
    def findall(pat: str, data: str) -> typing.Iterator[int]:
        """Iterator that give all position of a given pattern (no regex).

        Args:
            pat (str): Pattern to seek
            data (str): buffer

        Yields:
            int: Yields the next position

        """
        i = data.find(pat)
        while i != -1:
            yield i
            i = data.find(pat, i + 1)

    def get_raw_body_text(
        self,
        msg: email.message.Message,
    ) -> list[tuple[typing.Any, typing.Any, typing.Any]]:
        """This method recursively retrieves all e-mail body parts and returns them as a list.

        Args:
            msg (email.message.Message): The actual e-mail message or sub-message.

        Returns:
            list: Returns a list of sets which are in the form of "set(encoding, raw_body_string, message field headers)"

        """
        raw_body: list[tuple[typing.Any, typing.Any, typing.Any]] = []

        if msg.is_multipart():
            for part in msg.get_payload():
                raw_body.extend(self.get_raw_body_text(part))
        else:
            # Treat text document attachments as belonging to the body of the mail.
            # Attachments with a file-extension of .htm/.html are implicitly treated
            # as text as well in order not to escape later checks (e.g. URL scan).

            try:
                filename = msg.get_filename("").lower()
            except (binascii.Error, AssertionError):
                logger.exception(
                    "Exception occurred while trying to parse the content-disposition header. Collected data will not be complete.",
                )
                filename = ""

            # pylint: disable=too-many-boolean-expressions
            if (
                (
                    "content-disposition" not in msg
                    and msg.get_content_maintype() == "text"
                )
                or (filename.endswith(".html") or filename.endswith(".htm"))
                or (
                    "content-disposition" in msg
                    and msg.get_content_disposition() == "inline"
                    and msg.get_content_maintype() == "text"
                )
            ):
                encoding = msg.get("content-transfer-encoding", "").lower()

                charset = msg.get_content_charset()
                if charset is None:
                    raw_body_str = msg.get_payload(decode=True)
                    raw_body_str = EmailParserDecode.decode_string(raw_body_str, None)
                else:
                    try:
                        raw_body_str = msg.get_payload(decode=True).decode(
                            charset,
                            "ignore",
                        )
                    except (LookupError, ValueError):
                        logger.debug(
                            "An exception occurred while decoding the payload!",
                            exc_info=True,
                        )
                        raw_body_str = msg.get_payload(decode=True).decode(
                            "ascii",
                            "ignore",
                        )

                # In case we hit bug 27257 or any other parsing error, try to downgrade the used policy
                try:
                    raw_body.append((encoding, raw_body_str, msg.items()))
                except (AttributeError, TypeError):
                    former_policy: email.policy.Policy = msg.policy  # type: ignore
                    msg.policy = email.policy.compat32  # type: ignore
                    raw_body.append((encoding, raw_body_str, msg.items()))
                    msg.policy = former_policy  # type: ignore

        return raw_body

    @staticmethod
    def get_file_hash(data: bytes) -> dict[str, str]:
        """Generate hashes of various types (``MD5``, ``SHA-1``, ``SHA-256``, ``SHA-512``)\
        for the provided data.

        Args:
          data (bytes): The data to calculate the hashes on.

        Returns:
          dict: Returns a dict with as key the hash-type and value the calculated hash.

        """
        hashalgo = ["md5", "sha1", "sha256", "sha512"]
        hash_ = {}

        for k in hashalgo:
            ha = getattr(hashlib, k)
            h = ha()
            h.update(data)
            hash_[k] = h.hexdigest()

        return hash_

    @staticmethod
    def wrap_hash_sha256(string: str) -> str:
        """Generate a SHA256 hash for a given string.

        Args:
            string (str): String to calculate the hash on.

        Returns:
            str: Returns the calculated hash as a string.

        """
        _string = string.encode("utf-8")

        return hashlib.sha256(_string).hexdigest()

    def traverse_multipart(
        self,
        msg: email.message.Message,
        counter: int = 0,
    ) -> dict[str, typing.Any]:
        """Recursively traverses all e-mail message multi-part elements and returns in a parsed form as a dict.

        Args:
            msg (email.message.Message): An e-mail message object.
            counter (int, optional): A counter which is used for generating attachments
                file-names in case there are none found in the header. Default = 0.

        Returns:
            dict: Returns a dict with all original multi-part headers as well as generated hash check-sums,
                date size, file extension, real mime-type.

        """
        attachments = {}

        if msg.is_multipart():
            if "content-type" in msg:
                if msg.get_content_type() == "message/rfc822":
                    # This is an e-mail message attachment, add it to the attachment list apart from parsing it
                    attachments.update(
                        self.prepare_multipart_part_attachment(msg, counter),
                    )

            for part in msg.get_payload():
                attachments.update(self.traverse_multipart(part, counter))
        else:
            return self.prepare_multipart_part_attachment(msg, counter)

        return attachments

    def prepare_multipart_part_attachment(
        self,
        msg: email.message.Message,
        counter: int = 0,
    ) -> dict[str, typing.Any]:
        """Extract meta-information from a multipart-part.

        Args:
            msg (email.message.Message): An e-mail message object.
            counter (int, optional): A counter which is used for generating attachments
                file-names in case there are none found in the header. Default = 0.

        Returns:
            dict: Returns a dict with original multi-part headers as well as generated hash check-sums,
                date size, file extension, real mime-type.

        """
        attachment: dict[str, typing.Any] = {}

        # In case we hit bug 27257, try to downgrade the used policy
        try:
            lower_keys = [k.lower() for k in msg.keys()]
        except AttributeError:
            former_policy: email.policy.Policy = msg.policy  # type: ignore
            msg.policy = email.policy.compat32  # type: ignore
            lower_keys = [k.lower() for k in msg.keys()]
            msg.policy = former_policy  # type: ignore

        if (
            "content-disposition" in lower_keys
            and msg.get_content_disposition() != "inline"
        ) or msg.get_content_maintype() != "text":
            # if it's an attachment-type, pull out the filename
            # and calculate the size in bytes
            if msg.get_content_type() == "message/rfc822":
                payload = msg.get_payload()
                if len(payload) > 1:
                    logger.warning(
                        'More than one payload for "message/rfc822" part detected. This is not supported, please report!',
                    )

                try:
                    data = payload[0].as_bytes()
                except UnicodeEncodeError:
                    data = payload[0].as_bytes(policy=email.policy.compat32)

                file_size = len(data)
            else:
                data = msg.get_payload(decode=True)
                file_size = len(data)

            filename = msg.get_filename("")
            if filename == "":
                filename = f"part-{counter:03d}"
            else:
                filename = EmailParserDecode.decode_field(filename)

            file_id = str(uuid.uuid1())
            attachment[file_id] = {}
            attachment[file_id]["filename"] = filename
            attachment[file_id]["size"] = file_size

            # os.path always returns the extension as second element
            # in case there is no extension it returns an empty string
            extension = os.path.splitext(filename)[1].lower()
            if extension:
                # strip leading dot
                attachment[file_id]["extension"] = extension[1:]

            attachment[file_id]["hash"] = self.get_file_hash(data)

            mime_type, mime_type_short = self.get_mime_type(data)

            if not (mime_type is None or mime_type_short is None):
                attachment[file_id]["mime_type"] = mime_type
                # attachments[file_id]['mime_type_short'] = attachments[file_id]['mime_type'].split(",")[0]
                attachment[file_id]["mime_type_short"] = mime_type_short
            elif magic is not None:
                logger.warning(
                    f'Error determining attachment mime-type - "{file_id}"',
                )

            if self.include_attachment_data:
                attachment[file_id]["raw"] = (base64.b64encode(data)).decode("utf-8")

            ch: dict[str, list[str]] = {}
            for k, v in msg.items():
                k = k.lower()
                v = str(v)

                if k in ch:
                    ch[k].append(v)
                else:
                    ch[k] = [v]

            attachment[file_id]["content_header"] = ch

            counter += 1

        return attachment

    @staticmethod
    def get_mime_type(
        data: bytes,
    ) -> tuple[str, str] | tuple[None, None]:
        """Get mime-type information based on the provided bytes object.

        Args:
            data: Binary data.

        Returns:
            typing.Tuple[str, str]: Identified mime information and mime-type. If **magic** is not available, returns *None, None*.
                                    E.g. *"ELF 64-bit LSB shared object, x86-64, version 1 (SYSV)", "application/x-sharedlib"*

        """
        if magic is None:
            return None, None

        detected = magic.detect_from_content(data)
        return detected.name, detected.mime_type


def decode_email(
    eml_file: str,
    include_raw_body: bool = False,
    include_attachment_data: bool = False,
    pconf: dict | None = None,
    policy: email.policy.Policy = email.policy.default,
    ignore_bad_start: bool = False,
    email_force_tld: bool = False,
    parse_attachments: bool = True,
) -> dict:
    """Function for decoding an EML file into an easily parsable structure.

    Some intelligence is applied while parsing the file in order to work around
    broken files.
    Besides just parsing, this function also computes hashes and extracts meta
    information from the source file.

    .. deprecated:: 1.12.0

    Args:
      eml_file (str): Full absolute path to the file to be parsed.
      include_raw_body (bool, optional): Boolean parameter which indicates whether
                                         to include the original file contents in
                                         the returned structure. Default is False.
      include_attachment_data (bool, optional): Boolean parameter which indicates whether
                                                to include raw attachment data in the
                                                returned structure. Default is False.
      pconf (dict, optional): A dict with various optional configuration parameters,
                              e.g. allowlist IPs, allowlist e-mail addresses, etc.

      policy (email.policy.Policy, optional): Policy to use when parsing e-mails.
            Default = email.policy.default.

      ignore_bad_start (bool, optional): Ignore invalid file start. This has a considerable performance impact.

      email_force_tld (bool, optional): Only match e-mail addresses with a TLD. I.e exclude something like
                                        john@doe. By default this is disabled.

      parse_attachments (bool, optional): Set this to false if you want to disable the parsing of attachments.
                                          Please note that HTML attachments as well as other text data marked to be
                                          in-lined, will always be parsed.

    Returns:
      dict: A dictionary with the content of the EML parsed and broken down into
            key-value pairs.

    """
    warnings.warn(
        "You are using a deprecated method, please use the EmlParser class instead.",
        DeprecationWarning,
    )

    with open(eml_file, "rb") as fp:
        raw_email = fp.read()

    return decode_email_b(
        eml_file=raw_email,
        include_raw_body=include_raw_body,
        include_attachment_data=include_attachment_data,
        pconf=pconf,
        policy=policy,
        ignore_bad_start=ignore_bad_start,
        email_force_tld=email_force_tld,
        parse_attachments=parse_attachments,
    )


def decode_email_b(
    eml_file: bytes,
    include_raw_body: bool = False,
    include_attachment_data: bool = False,
    pconf: dict | None = None,
    policy: email.policy.Policy = email.policy.default,
    ignore_bad_start: bool = False,
    email_force_tld: bool = False,
    parse_attachments: bool = True,
) -> dict:
    """Function for decoding an EML file into an easily parsable structure.

    Some intelligence is applied while parsing the file in order to work around
    broken files.
    Besides just parsing, this function also computes hashes and extracts meta
    information from the source file.

    .. deprecated:: 1.12.0

    Args:
        eml_file (bytes): Contents of the raw EML file passed to this function as string.
        include_raw_body (bool, optional): Boolean parameter which indicates whether
                                           to include the original file contents in
                                           the returned structure. Default is False.
        include_attachment_data (bool, optional): Boolean parameter which indicates whether
                                                  to include raw attachment data in the
                                                  returned structure. Default is False.
        pconf (dict, optional): A dict with various optional configuration parameters,
                                e.g. allowlist IPs, allowlist e-mail addresses, etc.

        policy (email.policy.Policy, optional): Policy to use when parsing e-mails.
              Default = email.policy.default.

        ignore_bad_start (bool, optional): Ignore invalid file start. This has a considerable performance impact.

        email_force_tld (bool, optional): Only match e-mail addresses with a TLD. I.e exclude something like
                                          john@doe. By default this is disabled.

      parse_attachments (bool, optional): Set this to false if you want to disable the parsing of attachments.
                                          Please note that HTML attachments as well as other text data marked to be
                                          in-lined, will always be parsed.

    Returns:
        dict: A dictionary with the content of the EML parsed and broken down into
              key-value pairs.

    """
    warnings.warn(
        "You are using a deprecated method, please use the EmlParser class instead.",
        DeprecationWarning,
    )

    ep = EmlParser(
        include_raw_body=include_raw_body,
        include_attachment_data=include_attachment_data,
        pconf=pconf,
        policy=policy,
        ignore_bad_start=ignore_bad_start,
        email_force_tld=email_force_tld,
        parse_attachments=parse_attachments,
    )

    return ep.decode_email_bytes(eml_file)
