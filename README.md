# Bloom Garden

This is the service behind [Bloom Garden](https://garden.bloomcollective.xyz),
a public export of [Bloom Collective](https://bloomcollective.xyz)'s knowledge base.

The exporter service observes regular [Athens](https://github.com/athensresearch/athens)
dumps and regenerates the website when something changes. It relies on a
[slightly customized](https://github.com/knyar/athens) version of Athens that
writes a JSON content dump on every change.

The exporter uses:

- [ppeetteerrs/obsidian-zola](https://github.com/ppeetteerrs/obsidian-zola)
- [a custom version](https://github.com/knyar/athens-export) of
  [bshepherdson/athens-export](https://github.com/bshepherdson/athens-export)
- [zoni/obsidian-export](https://github.com/zoni/obsidian-export)
- [zola](https://github.com/getzola/zola)

## License

Licensed under MIT license.
