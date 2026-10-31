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

Results appear as a YAML document in a scratch view named **DBpedia Lookup**. Resource URIs are shown with each label and are clickable in Sublime Text; other fields supplied by the server are included as YAML values.

## Server configuration

By default, the plugin uses the public demo endpoint at `https://lookup.dbpedia.org`, see their [search page](https://www.dbpedia.org/resources/lookup/) for documentation. 

However, it is also possible to use your own, local endpoint for search. This way you can keep your searches private or use different search indexes. To use your own endpoint, change `default_server` to `local` in the user settings and enter the base URL of your local endpoint. The default local base URL is `http://localhost:8082`.

## Using a local endpoint

The source repository for the lookup application is [DBpedia Lookup - Generic RDF Indexer & Searcher](https://github.com/dbpedia/dbpedia-lookup). There is also an updated [`dbpedia/lookup` Docker image](https://hub.docker.com/r/dbpedia/lookup) for Docker, Podman available.

The source repository provides a docker-compose file that shows how to use the lookup app with raw data that gets indexed before it can used for search. However, you can also use pre-generated indexes from the dbpedia project. 

To find available index data, go to `https://databus.dbpedia.org/` and search for `lookup`. An example index would be https://databus.dbpedia.org/fhofer/collections/dbpedia-lookup-data. 

Example deployment:

```sh
docker-compose.yml
data/
	config.yml
	index/
		_3s0_Lucene99_0.tim 
		...
```

Docker compose example:

```yaml
version: "3.0"
services:
  lookup:
    image: "dbpedia/lookup:dev"
    ports:
      - 8082:8082
    environment:
      CONFIG_PATH: /resources/config.yml
    volumes:
      - ./data/:/resources/
```

Quickstart:

1. Uncompress the the contents of the downloded index of yor choice into the `data/index` folder
2. Copy the [config.yml](https://github.com/dbpedia/dbpedia-lookup/blob/main/examples/config.yml) from the source repositories' `examples` folder into your `data` folder
3. Change the `indexPath` in `config.yml` to `/resources/index`
4. Run `docker|podman compose up -d`


The plugin sends requests to `/api/search` at the configured base URL.

To check the API manually once the service is ready:

```sh
curl 'http://localhost:8082/api/search?query=Berlin&maxResults=5'
```

### Details

Check [server.md](https://github.com/dbpedia/dbpedia-lookup/blob/main/doc/server.md) for detailed configuration and change `config.yml` accordingly.

The API returns search documents under `docs`. The instance returns fields such as `id`, `label`, `typeName`, `type`, `category`, `refCount`, and `score` as lists; available fields depend on the index configuration. The plugin uses `id` as the resource URI and displays the other returned fields.

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
