# OPeNDAP and PyDAP Study Notes

## Scope

This note summarizes the parts of OPeNDAP and `pydap` that are most relevant to this repository: metadata inspection, remote data retrieval, and server-side subsetting.

## OPeNDAP in one sentence

OPeNDAP is a client-server protocol for remote access to scientific data in which a client can inspect metadata and request only selected variables or slices of arrays from a remote dataset, instead of downloading the whole file.

## Why that matters here

For `grep-dap`, the key value is not just remote access. It is the combination of:

- explicit structural metadata,
- optional and uneven semantic metadata,
- efficient remote sampling, and
- a standard mechanism for subsetting data and metadata.

That combination is exactly what makes incremental dataset characterization possible.

## Core OPeNDAP ideas

The NASA Earthdata OPeNDAP guide describes OPeNDAP as a client-server system in which a client requests data from a server, and the server can translate stored source data into the representation expected by the client. The same guide also emphasizes that OPeNDAP is useful for retrieval, sampling, and display of large distributed datasets rather than just full-file transfer.  
Source: <https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/opendap/user-guide>

### Metadata layers

The most important metadata-related responses are:

- `DDS`: Dataset Descriptor Structure. This describes the dataset’s structure, such as variables, arrays, dimensions, and compound types.
- `DAS`: Data Attribute Structure. This carries attributes such as units, names, conventions, and other descriptive metadata when providers supply them.
- `DDX`: an XML form that combines DDS and DAS.

This separation is important for this project because the `DDS` is structural and usually dependable, while the `DAS` is descriptive and may be sparse, inconsistent, or absent.

The Earthdata guide explicitly notes that the `DAS` is provider-populated and that its quality varies widely. That observation aligns directly with the problem statement in `AGENTS.md`.  
Sources:

- <https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/opendap>
- <https://opendap.github.io/documentation/UserGuideComprehensive.html>

### OPeNDAP data model

From the user-guide material, the main conceptual types worth tracking are:

- arrays and grids for regular multidimensional data,
- sequences for row-like observational or tabular data,
- structures for hierarchical grouping.

For unfamiliar datasets, that distinction already conveys useful information. A regular grid suggests fields on coordinates; a sequence suggests observations, events, or station-like records.

## Metadata inspection workflow

Based on the OPeNDAP documentation, a practical inspection workflow is:

1. Start with the dataset URL itself.
2. Request `.dds` to learn the structural layout.
3. Request `.das` to see available units, names, and attributes.
4. Request `.ddx` when an XML representation of both is easier to parse.
5. Use `.info` or the HTML form when a human-readable combined view is helpful.

The Earthdata guide also notes that adding `.html` to a dataset URL opens a server-side access form that helps construct requests interactively. That is useful for manual reconnaissance before automating a workflow.  
Source: <https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/opendap>

## Data retrieval and remote subsetting

The central mechanism is the OPeNDAP constraint expression appended to the dataset URL. The OPeNDAP user guide describes a constraint expression as having:

- a projection part, which chooses variables and array slices, and
- a selection part, which filters qualifying records.

In rough form:

```text
...?proj_1,proj_2,...&sel_1&sel_2...
```

For array-like data, the most important operation is projection with slicing. The Earthdata guide shows examples such as requesting only a portion of a coordinate vector or only a subset of a gridded variable. This is the part that makes "peek first, download later" possible.

Important details:

- Arrays and grids are commonly subset with index ranges.
- Strides can be used to subsample, not just crop.
- Sequence-like data supports record filtering through selection expressions.
- Servers may also expose extra services such as alternate encodings or helper forms.

For this project, the main implication is that characterization can be built from small, cheap probes:

- inspect structure,
- inspect attributes,
- fetch tiny slices,
- compare patterns,
- expand only when confidence improves.

## What `pydap` adds

`pydap` is a Python implementation of DAP/OPeNDAP. The `pydap` introduction emphasizes five practical benefits:

- it builds constraint expressions for the user,
- it escapes URL parameters safely,
- it can fetch binary data from DAP2 and DAP4 servers,
- it covers DAP2 and most of DAP4,
- it supports exploratory remote subsetting in a Pythonic way.

Source: <https://pydap.github.io/pydap/en/intro.html>

### Why `pydap` is useful here

For exploratory characterization, `pydap` turns remote probing into normal Python operations:

- open a remote dataset,
- inspect the variable tree,
- inspect per-variable attributes,
- slice remote arrays,
- pull only the selected data into memory.

That is a good fit for an inference-oriented workflow where many datasets may need quick, low-cost inspection.

### Client-side pattern

The standard entry point is `pydap.client.open_url`. The `pydap` documentation shows that this returns a dataset-like object, and remote variables can then be accessed by name.

Typical pattern:

```python
from pydap.client import open_url

dataset = open_url("http://test.opendap.org/dap/data/nc/coads_climatology.nc")
dataset.tree()
sst = dataset["SST"][0, 45:80, 45:125]
```

The important behavior is that slicing triggers server-side subsetting, so only the requested region is transferred. The `pydap` tutorial explicitly notes that slicing before download usually improves performance, especially for large datasets.  
Source: <https://pydap.github.io/pydap/en/ConstraintExpressions.html>

### Metadata inspection in `pydap`

The docs indicate several practical ways to inspect remote content without pulling large arrays:

- `dataset.tree()` for structure,
- variable access by key/name,
- variable attributes via `.attributes`,
- protocol-specific inspection for DAP4 datasets.

This is especially relevant to `grep-dap`: structure and attributes can be collected first, and numeric samples fetched only when needed.

### DAP2 and DAP4

The `pydap` protocol overview notes that there are two broad DAP data models, DAP2 and DAP4, with some differences in supported objects and types. In particular:

- `pydap` defaults to DAP2 unless told otherwise,
- DAP4 support matters for groups and newer types,
- some remote datasets may require `protocol="dap4"` when opened.

Source: <https://pydap.github.io/pydap/en/DAP_Protocol.html>

That distinction matters because a characterization tool may otherwise miss variables or structural detail if it assumes the wrong protocol.

## Practical takeaways for `grep-dap`

### What OPeNDAP reliably gives you

- variable names,
- array shapes and dimensionality,
- type information,
- hierarchical structure,
- coordinate/map variables in many datasets,
- optional descriptive attributes,
- efficient access to small data samples.

### What it does not guarantee

- trustworthy semantic labels,
- complete units and provenance,
- consistent metadata conventions across providers,
- enough documentation to interpret variables directly.

### A sensible study-phase conclusion

For this repository, OPeNDAP should be treated as a structured probing interface rather than just a download mechanism. Its strongest contribution is that it exposes enough syntax and enough sample access to support iterative inference.

`pydap` appears to be the right Python tool for that first layer because it lowers the cost of:

- enumerating structure,
- checking attributes,
- sampling arrays and sequences,
- automating repeated probes across many servers.

## Implications for GenAI-assisted characterization

Given the project framing in `AGENTS.md`, the useful role of GenAI is not to replace protocol-level inspection. It is to combine weak signals retrieved through OPeNDAP:

- names from DDS/DAS,
- shapes and dimensionality,
- coordinate relationships,
- small numeric samples,
- directory or catalog context,
- similarity to known reference datasets.

That suggests a pipeline like:

1. Use OPeNDAP or `pydap` to gather structural metadata and tiny samples.
2. Normalize those observations into a compact representation.
3. Ask downstream heuristics or models to infer likely variable meaning, dataset class, or confidence-ranked hypotheses.

In other words, OPeNDAP supplies the evidence channel; GenAI would sit above that channel as an interpretation layer.

## Sources

- NASA Earthdata OPeNDAP overview: <https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/opendap>
- NASA Earthdata OPeNDAP User Guide: <https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/opendap/user-guide>
- OPeNDAP User Guide (OPeNDAP project): <https://opendap.github.io/documentation/UserGuideComprehensive.html>
- PyDAP introduction: <https://pydap.github.io/pydap/en/intro.html>
- PyDAP constraint expressions: <https://pydap.github.io/pydap/en/ConstraintExpressions.html>
- PyDAP DAP protocol overview: <https://pydap.github.io/pydap/en/DAP_Protocol.html>
