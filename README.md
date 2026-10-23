# sublime-dbpedia-lookup

A Sublime Text 4 plugin for the [DBpedia Lookup](https://github.com/dbpedia/dbpedia-lookup) service.

## Install in Sublime Text 4

Copy `DBpediaLookup.sublime-package` into Sublime Text's `Installed Packages` directory and restart Sublime Text. On macOS, the directory is `~/Library/Application Support/Sublime Text/Installed Packages/`.

## Use case

This plugin provides quick context lookups while reading or editing a text. Select a phrase, or place the cursor on a word, and run **DBpedia Lookup**. The plugin searches the DBpedia Lookup service and displays matching resources and their indexed properties in a reusable scratch view.

## Usage

The plugin provides a command in the context menu:

* Right-click a selection and choose **DBpedia Lookup** to search the selection.
* Right-click at a word and choose **DBpedia Lookup** to search that word.

Results appear in a scratch view named **DBpedia Lookup**. Resource URIs are shown alongside labels and any other fields supplied by the server.

## Server configuration

By default, the plugin uses the public demo endpoint at `https://lookup.dbpedia.org`. To use it locally, change `default_server` to `local` in the user settings. The default local base URL is `http://localhost:8082`.

The local service runs the updated [`dbpedia/lookup` Docker image](https://hub.docker.com/r/dbpedia/lookup). The plugin sends requests to `/api/search` at the configured base URL.

To check the API manually once the service is ready:

```sh
curl 'http://localhost:8082/api/search?query=Berlin&maxResults=5'
```

The API returns search documents under `docs`. The LAN instance returns fields such as `id`, `label`, `typeName`, `type`, `category`, `refCount`, and `score` as lists; available fields depend on the index configuration. The plugin uses `id` as the resource URI and displays the other returned fields.

## Development and testing

1. Make sure the `dbpedia/lookup` service is running and its index is ready.
2. In Sublime Text 4, install or symlink this repository as a package, then select `Berlin` in a text file and run **DBpedia Lookup** from the context menu.
3. Repeat with the cursor inside a word and confirm that results appear in the **DBpedia Lookup** scratch view.
4. Set `default_server` to `local` and confirm the request reaches the LAN service. Also try a term with no matches and verify the status message.

For local service checks, use the published Docker image; do not build the DBpedia Lookup image.

## Limitations

Results depend on the fields present in the server's configured index. The plugin displays available fields without assuming that every preset provides the same metadata.

## License

This plugin is available under the [MIT License](LICENSE).
