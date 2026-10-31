import json
import logging
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import sublime
import sublime_plugin


logger = logging.getLogger("DBpedia Lookup")


class DbpediaLookupReplaceResultsCommand(sublime_plugin.TextCommand):
    def run(self, edit, contents):
        self.view.set_read_only(False)
        self.view.run_command("select_all")
        self.view.run_command("right_delete")
        self.view.insert(edit, 0, contents)
        self.fold_property_lists()
        self.view.set_read_only(True)

    def fold_property_lists(self):
        text = self.view.substr(sublime.Region(0, self.view.size()))
        offset = 0
        list_start = None
        list_end = None
        previous_line_end = 0

        for line in text.splitlines(True):
            if line.startswith("      - "):
                if list_start is None:
                    # Begin folding at the end of the YAML key line so Sublime
                    # puts the fold marker beside the key, not on the first item.
                    list_start = previous_line_end
                list_end = offset + len(line.rstrip("\r\n"))
            elif list_start is not None:
                self.view.fold(sublime.Region(list_start, list_end))
                list_start = None
            previous_line_end = offset + len(line.rstrip("\r\n"))
            offset += len(line)

        if list_start is not None:
            self.view.fold(sublime.Region(list_start, list_end))


class DbpediaLookupCommand(sublime_plugin.TextCommand):
    VIEW_NAME = "DBpedia Lookup"
    MAX_HITS = 5

    def run(self, edit):
        selections = self.view.sel()
        if not selections:
            return

        selection = selections[0]
        if selection.empty():
            lookup_item = self.view.substr(self.view.word(selection.begin()))
        else:
            lookup_item = self.view.substr(selection)

        lookup_item = lookup_item.strip()
        if not lookup_item:
            sublime.status_message("DBpedia Lookup: select a term or place the cursor on a word")
            return

        logger.info("DBpedia: looking up %s", lookup_item)
        results = self.lookup(lookup_item)
        if results is None:
            return

        documents = results.get("docs", [])
        if not isinstance(documents, list) or not documents:
            sublime.status_message('DBpedia Lookup: no results for "{}"'.format(lookup_item))
            return

        contents = self.output(documents, lookup_item)
        result_view = self.get_view()
        result_view.set_syntax_file("Packages/YAML/YAML.sublime-syntax")
        result_view.run_command("dbpedia_lookup_replace_results", {"contents": contents})

        sublime.active_window().focus_view(result_view)

    def output(self, documents, lookup_item):
        lines = ["query: {}".format(self.yaml_scalar(lookup_item)), "results:"]
        for document in documents:
            if not isinstance(document, dict):
                continue

            resource = self.first_value(document.get("resource")) or self.first_value(
                document.get("id")
            )
            label = self.first_value(document.get("label")) or resource or "Result"
            lines.append("  - label: {}".format(self.yaml_scalar(label)))
            if resource:
                lines.append("    uri: {}".format(self.yaml_scalar(resource)))

            description = self.first_value(document.get("comment"))
            if description:
                lines.append("    description: {}".format(self.yaml_scalar(description)))

            for field, value in document.items():
                if field in ("resource", "id", "label", "comment"):
                    continue
                values = self.values(value)
                if values:
                    key = self.yaml_scalar(field)
                    if field in ("score", "refCount"):
                        numeric_value = self.numeric_value(values[0], field)
                        lines.append(
                            "    {}: {}".format(key, self.yaml_scalar(numeric_value))
                        )
                    elif isinstance(value, list):
                        lines.append("    {}:".format(key))
                        lines.extend(
                            "      - {}".format(self.yaml_scalar(item))
                            for item in values
                        )
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        lines.append("    {}: {}".format(key, self.yaml_scalar(value)))
                    else:
                        lines.append(
                            "    {}: {}".format(key, self.yaml_scalar(values[0]))
                        )

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def values(value):
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        values = []
        for item in value:
            if isinstance(item, dict):
                item = item.get("value", "")
            if item is not None:
                text = re.sub(r"<[^>]*>", "", str(item))
                values.append(unescape(text))
        return values

    @staticmethod
    def numeric_value(value, field):
        """Convert numeric API fields, which may arrive as one-element string lists."""
        try:
            return int(value) if field == "refCount" else float(value)
        except (TypeError, ValueError):
            return value

    @staticmethod
    def yaml_scalar(value):
        """Render a readable YAML string, quoting only ambiguous or unsafe values."""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        value = str(value)
        ambiguous = re.match(
            r"^(?:null|true|false|yes|no|on|off|[-+]?(?:[0-9].*|\.inf|\.nan))$",
            value,
            re.IGNORECASE,
        )
        unsafe = (
            not value
            or value != value.strip()
            or value[0] in "-?:,[]{}#&*!|>'\"%@`"
            or ": " in value
            or re.search(r"\s#", value)
            or any(ord(char) < 32 for char in value)
        )
        return json.dumps(value, ensure_ascii=False) if unsafe or ambiguous else value

    @classmethod
    def first_value(cls, value):
        values = cls.values(value)
        return values[0] if values else ""

    def get_view(self):
        for window in sublime.windows():
            for view in window.views():
                if view.name() == self.VIEW_NAME:
                    return view

        view = sublime.active_window().new_file()
        view.set_encoding("utf-8")
        view.set_name(self.VIEW_NAME)
        view.set_scratch(True)
        view.set_syntax_file("Packages/YAML/YAML.sublime-syntax")
        return view

    def lookup(self, name):
        settings = sublime.load_settings("dbpedia_lookup.sublime-settings")
        if settings.get("default_server", "remote") == "remote":
            host = settings.get(
                "dbpedia_lookup_server_remote", "https://lookup.dbpedia.org"
            )
        else:
            host = settings.get(
                "dbpedia_lookup_server_local",
                "http://localhost:8082",
            )

        params = {"query": name, "maxResults": self.MAX_HITS, "format": "JSON"}
        request = Request(
            host.rstrip("/") + "/api/search?" + urlencode(params),
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("The Lookup API returned an unexpected response")
            documents = payload.get("docs")
            if not isinstance(documents, list):
                raise ValueError("The Lookup API response did not contain a docs list")
            return payload
        except HTTPError as error:
            message = "DBpedia Lookup: HTTP error {} contacting {}".format(
                error.code, host
            )
        except URLError as error:
            message = "DBpedia Lookup: could not contact {} ({})".format(
                host, error.reason
            )
        except (TimeoutError, OSError) as error:
            message = "DBpedia Lookup: could not contact {} ({})".format(host, error)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            message = "DBpedia Lookup: invalid API response ({})".format(error)

        logger.error(message)
        sublime.error_message(message)
        return None
