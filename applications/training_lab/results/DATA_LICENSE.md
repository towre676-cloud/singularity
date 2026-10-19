# Evaluation data provenance

The WikiText-2 source is Stephen Merity and collaborators' [Salesforce/WikiText dataset](https://huggingface.co/datasets/Salesforce/wikitext), based on Wikipedia articles. The pinned revision and source attribution appear in [wikitext_source_manifest.json](wikitext_source_manifest.json). Its declared licenses are [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) and [GFDL](https://www.gnu.org/licenses/fdl-1.3.html); retain this attribution and the source's licensing terms when redistributing source-derived evaluation excerpts.

The full source text and parquet files are obtained through the pinned download script. Some new NPZ audit archives retain selected target byte values alongside numerical losses and causal weights, so their evaluation excerpts are source-derived data. Model predictions and numerical receipts also bind their source intervals and hashes. The repository's code license does not replace the source dataset's licenses.
