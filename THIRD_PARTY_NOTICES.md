# Third-party notices

Audit snapshot: 2026-10-19, fresh CPython 3.12 / macOS arm64 install. Project MIT terms apply only to original code. Dependencies, fonts, and native libraries retain their own licenses. Exact upstream license/NOTICE texts are preserved under [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES/); retain that directory with this notice. No upstream dependency was modified.

Install the audited runtime with `pip install -r requirements.txt` (which constrains the full resolution with `requirements-lock.txt`), or tests with `pip install -r requirements-dev.txt`. Other operating systems may add platform-specific dependencies; re-inventory a binary release on its target platform.

## Runtime dependencies

| Component | Version | License / class | Source | Preserved terms |
|---|---|---|---|---|
| altair | 6.3.0 | BSD-3-Clause / permissive | [upstream](https://github.com/vega/altair) | [LICENSE](THIRD_PARTY_LICENSES/altair/altair-6.3.0.dist-info/licenses/LICENSE) |
| anyio | 4.15.1 | MIT / permissive | [upstream](https://pypi.org/project/anyio/4.15.1/) | [LICENSE](THIRD_PARTY_LICENSES/anyio/anyio-4.15.1.dist-info/licenses/LICENSE) |
| attrs | 26.1.0 | MIT / permissive | [upstream](https://pypi.org/project/attrs/26.1.0/) | [LICENSE](THIRD_PARTY_LICENSES/attrs/attrs-26.1.0.dist-info/licenses/LICENSE) |
| certifi | 2026.10.18 | MPL-2.0 / weak copyleft | [upstream](https://github.com/certifi/python-certifi) | [LICENSE](THIRD_PARTY_LICENSES/certifi/certifi-2026.10.18.dist-info/licenses/LICENSE) |
| charset-normalizer | 3.5.2 | MIT / permissive | [upstream](https://pypi.org/project/charset-normalizer/3.5.2/) | [LICENSE](THIRD_PARTY_LICENSES/charset-normalizer/charset_normalizer-3.5.2.dist-info/licenses/LICENSE) |
| click | 8.5.0 | BSD-3-Clause / permissive | [upstream](https://github.com/pallets/click/) | [LICENSE.txt](THIRD_PARTY_LICENSES/click/click-8.5.0.dist-info/licenses/LICENSE.txt) |
| contourpy | 1.4.0 | BSD-3-Clause / permissive | [upstream](https://github.com/contourpy/contourpy) | [LICENSE](THIRD_PARTY_LICENSES/contourpy/contourpy-1.4.0.dist-info/licenses/LICENSE) |
| cycler | 0.12.1 | BSD-3-Clause / permissive | [upstream](https://matplotlib.org/cycler/) | [LICENSE](THIRD_PARTY_LICENSES/cycler/cycler-0.12.1.dist-info/LICENSE) |
| fonttools | 4.67.0 | MIT / permissive | [upstream](http://github.com/fonttools/fonttools) | [LICENSE](THIRD_PARTY_LICENSES/fonttools/fonttools-4.67.0.dist-info/licenses/LICENSE), [LICENSE.external](THIRD_PARTY_LICENSES/fonttools/fonttools-4.67.0.dist-info/licenses/LICENSE.external) |
| h11 | 0.16.0 | MIT / permissive | [upstream](https://github.com/python-hyper/h11) | [LICENSE.txt](THIRD_PARTY_LICENSES/h11/h11-0.16.0.dist-info/licenses/LICENSE.txt) |
| idna | 3.20 | BSD-3-Clause / permissive | [upstream](https://github.com/kjd/idna) | [LICENSE.md](THIRD_PARTY_LICENSES/idna/idna-3.20.dist-info/licenses/LICENSE.md) |
| itsdangerous | 2.2.0 | BSD-3-Clause / permissive | [upstream](https://github.com/pallets/itsdangerous/) | [LICENSE.txt](THIRD_PARTY_LICENSES/itsdangerous/itsdangerous-2.2.0.dist-info/LICENSE.txt) |
| Jinja2 | 3.1.6 | BSD-3-Clause / permissive | [upstream](https://github.com/pallets/jinja/) | [LICENSE.txt](THIRD_PARTY_LICENSES/jinja2/jinja2-3.1.6.dist-info/licenses/LICENSE.txt) |
| jsonschema | 4.26.0 | MIT / permissive | [upstream](https://github.com/python-jsonschema/jsonschema) | [COPYING](THIRD_PARTY_LICENSES/jsonschema/jsonschema-4.26.0.dist-info/licenses/COPYING) |
| jsonschema-specifications | 2025.9.1 | MIT / permissive | [upstream](https://github.com/python-jsonschema/jsonschema-specifications) | [COPYING](THIRD_PARTY_LICENSES/jsonschema-specifications/jsonschema_specifications-2025.9.1.dist-info/licenses/COPYING) |
| kiwisolver | 1.5.1 | BSD-3-Clause / permissive | [upstream](https://github.com/nucleic/kiwi) | [LICENSE](THIRD_PARTY_LICENSES/kiwisolver/kiwisolver-1.5.1.dist-info/licenses/LICENSE) |
| MarkupSafe | 3.0.4 | BSD-3-Clause / permissive | [upstream](https://github.com/pallets/markupsafe/) | [LICENSE.txt](THIRD_PARTY_LICENSES/markupsafe/markupsafe-3.0.4.dist-info/licenses/LICENSE.txt) |
| matplotlib | 3.11.2 | Matplotlib (PSF-based permissive license) / permissive | [upstream](https://matplotlib.org) | [LICENSE](THIRD_PARTY_LICENSES/matplotlib/matplotlib-3.11.2.dist-info/LICENSE), [LICENSE_DEJAVU](THIRD_PARTY_LICENSES/matplotlib/matplotlib/mpl-data/fonts/ttf/LICENSE_DEJAVU), [LICENSE_STIX](THIRD_PARTY_LICENSES/matplotlib/matplotlib/mpl-data/fonts/ttf/LICENSE_STIX) |
| narwhals | 2.27.1 | MIT / permissive | [upstream](https://github.com/narwhals-dev/narwhals) | [LICENSE.md](THIRD_PARTY_LICENSES/narwhals/narwhals-2.27.1.dist-info/licenses/LICENSE.md) |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 / permissive | [upstream](https://numpy.org) | [LICENSE.txt](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/LICENSE.txt), [LICENSE.txt](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/_core/include/numpy/libdivide/LICENSE.txt), [COPYING](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/_core/src/common/pythoncapi-compat/COPYING), [LICENSE](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/_core/src/highway/LICENSE), [dragon4_LICENSE.txt](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/_core/src/multiarray/dragon4_LICENSE.txt), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/_core/src/npysort/x86-simd-sort/LICENSE.md), [LICENSE](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/_core/src/umath/svml/LICENSE), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/fft/pocketfft/LICENSE.md), [LICENSE.txt](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/linalg/lapack_lite/LICENSE.txt), [LICENSE](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/ma/LICENSE), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/random/LICENSE.md), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/random/src/distributions/LICENSE.md), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/random/src/mt19937/LICENSE.md), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/random/src/pcg64/LICENSE.md), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/random/src/philox/LICENSE.md), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/random/src/sfc64/LICENSE.md), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy-2.5.4.dist-info/licenses/numpy/random/src/splitmix64/LICENSE.md), [LICENSE.txt](THIRD_PARTY_LICENSES/numpy/numpy/_core/include/numpy/random/LICENSE.txt), [LICENSE](THIRD_PARTY_LICENSES/numpy/numpy/ma/LICENSE), [LICENSE.md](THIRD_PARTY_LICENSES/numpy/numpy/random/LICENSE.md) |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause / permissive | [upstream](https://github.com/pypa/packaging) | [LICENSE](THIRD_PARTY_LICENSES/packaging/packaging-26.3.dist-info/licenses/LICENSE), [LICENSE.APACHE](THIRD_PARTY_LICENSES/packaging/packaging-26.3.dist-info/licenses/LICENSE.APACHE), [LICENSE.BSD](THIRD_PARTY_LICENSES/packaging/packaging-26.3.dist-info/licenses/LICENSE.BSD) |
| pandas | 3.0.6 | BSD-3-Clause / permissive | [upstream](https://pandas.pydata.org) | [LICENSE](THIRD_PARTY_LICENSES/pandas/pandas-3.0.6.dist-info/LICENSE) |
| pillow | 12.3.0 | MIT-CMU / permissive | [upstream](https://python-pillow.github.io) | [LICENSE](THIRD_PARTY_LICENSES/pillow/pillow-12.3.0.dist-info/licenses/LICENSE) |
| plotly | 7.1.0 | MIT / permissive | [upstream](https://plotly.com/python/) | [LICENSE.txt](THIRD_PARTY_LICENSES/plotly/plotly-7.1.0.dist-info/licenses/LICENSE.txt), [third-party-licenses.json](THIRD_PARTY_LICENSES/plotly/plotly/labextension/static/third-party-licenses.json) |
| protobuf | 7.36.2 | BSD-3-Clause / permissive | [upstream](https://developers.google.com/protocol-buffers/) | [LICENSE](THIRD_PARTY_LICENSES/protobuf/protobuf-7.36.2.dist-info/LICENSE) |
| pyarrow | 26.0.0 | Apache-2.0 / permissive | [upstream](https://arrow.apache.org/) | [LICENSE.txt](THIRD_PARTY_LICENSES/pyarrow/pyarrow-26.0.0.dist-info/licenses/LICENSE.txt), [NOTICE.txt](THIRD_PARTY_LICENSES/pyarrow/pyarrow-26.0.0.dist-info/licenses/NOTICE.txt) |
| pydeck | 0.9.3 | Apache-2.0 / permissive | [upstream](https://github.com/visgl/deck.gl/tree/master/bindings/pydeck) | [LICENSE.txt](THIRD_PARTY_LICENSES/pydeck/pydeck-0.9.3.dist-info/licenses/LICENSE.txt) |
| pyparsing | 3.3.3 | MIT / permissive | [upstream](https://github.com/pyparsing/pyparsing/) | [LICENSE](THIRD_PARTY_LICENSES/pyparsing/pyparsing-3.3.3.dist-info/licenses/LICENSE) |
| python-dateutil | 2.9.0.post0 | BSD-3-Clause OR Apache-2.0 / permissive | [upstream](https://github.com/dateutil/dateutil) | [LICENSE](THIRD_PARTY_LICENSES/python-dateutil/python_dateutil-2.9.0.post0.dist-info/LICENSE) |
| python-multipart | 0.0.32 | Apache-2.0 / permissive | [upstream](https://github.com/Kludex/python-multipart) | [LICENSE.txt](THIRD_PARTY_LICENSES/python-multipart/python_multipart-0.0.32.dist-info/licenses/LICENSE.txt) |
| referencing | 0.37.0 | MIT / permissive | [upstream](https://github.com/python-jsonschema/referencing) | [COPYING](THIRD_PARTY_LICENSES/referencing/referencing-0.37.0.dist-info/licenses/COPYING) |
| requests | 2.34.2 | Apache-2.0 / permissive | [upstream](https://github.com/psf/requests) | [LICENSE](THIRD_PARTY_LICENSES/requests/requests-2.34.2.dist-info/licenses/LICENSE), [NOTICE](THIRD_PARTY_LICENSES/requests/requests-2.34.2.dist-info/licenses/NOTICE) |
| rpds-py | 2026.9.1 | MIT / permissive | [upstream](https://github.com/crate-py/rpds) | [LICENSE](THIRD_PARTY_LICENSES/rpds-py/rpds_py-2026.9.1.dist-info/licenses/LICENSE) |
| scipy | 1.18.1 | BSD-3-Clause / permissive | [upstream](https://scipy.org/) | [LICENSE.txt](THIRD_PARTY_LICENSES/scipy/scipy-1.18.1.dist-info/LICENSE.txt), [LICENSE](THIRD_PARTY_LICENSES/scipy/scipy/_lib/_uarray/LICENSE), [LICENSE.md](THIRD_PARTY_LICENSES/scipy/scipy/fft/_duccfft/LICENSE.md), [LICENSE_DOP](THIRD_PARTY_LICENSES/scipy/scipy/integrate/LICENSE_DOP), [COPYING_QHULL.txt](THIRD_PARTY_LICENSES/scipy/scipy/spatial/qhull_src/COPYING_QHULL.txt) |
| six | 1.17.0 | MIT / permissive | [upstream](https://github.com/benjaminp/six) | [LICENSE](THIRD_PARTY_LICENSES/six/six-1.17.0.dist-info/LICENSE) |
| starlette | 1.9.0 | BSD-3-Clause / permissive | [upstream](https://github.com/Kludex/starlette) | [LICENSE.md](THIRD_PARTY_LICENSES/starlette/starlette-1.9.0.dist-info/licenses/LICENSE.md) |
| streamlit | 1.66.0 | Apache-2.0 / permissive | [upstream](https://streamlit.io) | [Source-Serif.LICENSE](THIRD_PARTY_LICENSES/streamlit/upstream/Source-Serif.LICENSE), [Source-Sans.LICENSE](THIRD_PARTY_LICENSES/streamlit/upstream/Source-Sans.LICENSE), [LICENSE](THIRD_PARTY_LICENSES/streamlit/upstream/LICENSE), [Open-Iconic.LICENSE](THIRD_PARTY_LICENSES/streamlit/upstream/Open-Iconic.LICENSE), [Source-Code.LICENSE](THIRD_PARTY_LICENSES/streamlit/upstream/Source-Code.LICENSE), [NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES), [Material-Icons.LICENSE](THIRD_PARTY_LICENSES/streamlit/upstream/Material-Icons.LICENSE) |
| typing_extensions | 4.16.0 | PSF-2.0 / permissive | [upstream](https://github.com/python/typing_extensions) | [LICENSE](THIRD_PARTY_LICENSES/typing-extensions/typing_extensions-4.16.0.dist-info/licenses/LICENSE) |
| urllib3 | 2.8.0 | MIT / permissive | [upstream](https://pypi.org/project/urllib3/2.8.0/) | [LICENSE.txt](THIRD_PARTY_LICENSES/urllib3/urllib3-2.8.0.dist-info/licenses/LICENSE.txt) |
| uvicorn | 0.54.0 | BSD-3-Clause / permissive | [upstream](https://uvicorn.dev/) | [LICENSE.md](THIRD_PARTY_LICENSES/uvicorn/uvicorn-0.54.0.dist-info/licenses/LICENSE.md) |
| websockets | 17.3 | BSD-3-Clause / permissive | [upstream](https://github.com/python-websockets/websockets) | [LICENSE](THIRD_PARTY_LICENSES/websockets/websockets-17.3.dist-info/licenses/LICENSE) |

## Development and tests only

| Component | Version | License / class | Source | Preserved terms |
|---|---|---|---|---|
| iniconfig | 2.3.1 | MIT / permissive | [upstream](https://github.com/pytest-dev/iniconfig) | [LICENSE](THIRD_PARTY_LICENSES/iniconfig/iniconfig-2.3.1.dist-info/licenses/LICENSE) |
| pluggy | 1.7.0 | MIT / permissive | [upstream](https://github.com/pytest-dev/pluggy) | [LICENSE](THIRD_PARTY_LICENSES/pluggy/pluggy-1.7.0.dist-info/licenses/LICENSE) |
| Pygments | 2.21.0 | BSD-2-Clause / permissive | [upstream](https://pygments.org) | [LICENSE](THIRD_PARTY_LICENSES/pygments/pygments-2.21.0.dist-info/licenses/LICENSE) |
| pytest | 9.1.1 | MIT / permissive | [upstream](https://docs.pytest.org/en/latest/) | [LICENSE](THIRD_PARTY_LICENSES/pytest/pytest-9.1.1.dist-info/licenses/LICENSE) |

## Copyleft and redistribution

certifi’s Mozilla CA certificate bundle is MPL-2.0, used unmodified. Retain the MPL text and source availability for the covered files when redistributing it; this file-level obligation does not relicense the application. Source: https://github.com/certifi/python-certifi .

## Components inside dependency wheels

These are not additional pip dependencies. Their exact upstream notices are included in the parent package’s preserved files. Classification follows the actual grants, including standard permissive variants (MIT-CMU, PSF-based Matplotlib, Qhull, FreeType/FTL, Bitstream and BaKoMa); an “all rights reserved” preamble followed by an explicit redistribution grant is not a proprietary restriction.

| Component | Version / parent | License and obligations | Source |
|---|---|---|---|
| Streamlit Source Code, Source Sans, Source Serif fonts | Bundled in audited Streamlit version | OFL-1.1, weak copyleft limited to font software; preserve OFL and reserved font names; no standalone font sales. Font software stays OFL; documents and application stay under their own terms. | https://github.com/streamlit/streamlit/tree/develop/frontend/app/src/assets/fonts |
| Streamlit Material Symbols / icons; Open Iconic | Bundled in audited Streamlit version | Apache-2.0; MIT respectively. Preserved font/icon notices in streamlit/upstream. | https://github.com/streamlit/streamlit |
| NumPy bundled algorithms (Highway, libdivide, PCG, Random123, pocketfft, LAPACK-lite, SVML, dragon4, pythoncapi-compat) | Audited NumPy wheel | BSD / MIT / 0BSD / Zlib / CC0; exact notices preserved under numpy. A wheel’s license text can describe libraries absent on this platform. | https://github.com/numpy/numpy |
| SciPy OpenBLAS/LAPACK, uarray, ducc, DOP | Audited SciPy wheel | BSD variants; retained attribution. | https://github.com/scipy/scipy |
| SciPy libgcc_s and libgfortran native runtime | Audited SciPy wheel | GPL-3.0-or-later WITH GCC-exception-3.1 (strong-copyleft license with runtime exception). The exception permits eligible independent application code under MIT; preserve notices and meet covered runtime source obligations on redistribution. | https://gcc.gnu.org/onlinedocs/libstdc++/manual/license.html |
| SciPy libquadmath native runtime | Audited SciPy wheel | LGPL-2.1-or-later (weak copyleft); dynamically linked unmodified. Retain LGPL and provide the corresponding runtime source / relinking rights when redistributing the binary. | https://gcc.gnu.org/onlinedocs/libquadmath/ |
| Matplotlib STIX, LastResort and AMS fonts | Audited Matplotlib wheel | OFL-1.1 (font-only weak copyleft); preserve license/reserved names. | https://github.com/matplotlib/matplotlib |
| Adobe PDF core-font AFM metrics | Bundled in audited Matplotlib wheel | Explicit permissive use/copy/distribution grant; retain original copyright and the accompanying [Adobe readme](THIRD_PARTY_LICENSES/matplotlib/Adobe-AFM-readme.txt). These are metrics, not Apple or Adobe font programs. | https://github.com/matplotlib/matplotlib/tree/main/lib/matplotlib/mpl-data/fonts/pdfcorefonts |
| Matplotlib DejaVu / Bitstream, BaKoMa fonts | Audited Matplotlib wheel | Bitstream-Vera / BaKoMa permissive redistribution grants, with notices and naming restrictions; no Apple/system fonts are bundled. | https://github.com/matplotlib/matplotlib |
| Matplotlib FreeType, HarfBuzz, Qhull, libraqm, SheenBidi, colormaps | Audited Matplotlib wheel | FTL selected instead of GPL; MIT / Qhull / Apache-2.0 / CC0. Full bundled terms and notices in matplotlib’s LICENSE. | https://github.com/matplotlib/matplotlib |

## Streamlit bundled frontend inventory

This is the upstream NOTICES inventory, which may be broader than the installed runtime bundle. Versions come from the same release’s frontend/yarn.lock; multiple resolutions are listed conservatively. Assets not separately versioned by upstream are tied to the Streamlit release. JSZip’s offered MIT option is selected. All required notice text, including dependency attributions, is reproduced verbatim in [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES).

| Component | Version | License / class | Source | Preserved terms |
|---|---|---|---|---|
| @antfu/install-pkg | 1.1.0 | MIT / permissive | [upstream](https://github.com/antfu/install-pkg.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @babel/code-frame, @babel/generator, @babel/helper-globals, @babel/helper-module-imports, @babel/helper-string-parser, @babel/helper-validator-identifier, @babel/runtime, @babel/template, @babel/traverse, @babel/types | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/babel/babel.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @babel/parser | 7.29.7 | MIT / permissive | [upstream](https://github.com/babel/babel.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @braintree/sanitize-url | 7.1.2 | MIT / permissive | [upstream](https://github.com/braintree/sanitize-url.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @carto/api-client | 0.5.24 | MIT / permissive | [upstream](https://github.com/CartoDB/carto-api-client.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @chevrotain/types, dompurify, flatbuffers, long | bundled with Streamlit 1.66.0; upstream notice gives no separate version | Apache-2.0 / permissive | [upstream](https://github.com/Chevrotain/chevrotain.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @deck.gl/aggregation-layers, @deck.gl/carto, @deck.gl/core, @deck.gl/extensions, @deck.gl/geo-layers, @deck.gl/json, @deck.gl/layers, @deck.gl/mesh-layers, @deck.gl/react, @deck.gl/widgets, @probe.gl/env, @probe.gl/log, @probe.gl/stats | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/visgl/deck.gl.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @emotion/babel-plugin, @emotion/cache, @emotion/hash, @emotion/is-prop-valid, @emotion/memoize, @emotion/react, @emotion/serialize, @emotion/sheet, @emotion/styled, @emotion/unitless, @emotion/use-insertion-effect-with-fallbacks, @emotion/utils, @emotion/weak-memoize | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/emotion-js/emotion/tree/main/packages/babel-plugin) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @floating-ui/core, @floating-ui/dom, @floating-ui/react, @floating-ui/utils | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/floating-ui/floating-ui.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @glideapps/glide-data-grid, @glideapps/glide-data-grid-cells, @glideapps/glide-data-grid-source | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/glideapps/glide-data-grid.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @hpcc-js/wasm | 2.22.4 | Apache-2.0 / permissive | [upstream](https://github.com/hpcc-systems/hpcc-js-wasm.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @iconify/types | 2.0.0 | MIT / permissive | [upstream](https://github.com/iconify/iconify.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @iconify/utils | 3.1.3 | MIT / permissive | [upstream](https://github.com/iconify/iconify.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @internationalized/date, @internationalized/number, @internationalized/string, react-aria, react-aria-components, react-stately | bundled with Streamlit 1.66.0; upstream notice gives no separate version | Apache-2.0 / permissive | [upstream](https://github.com/adobe/react-spectrum/tree/main/packages/@internationalized/date) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @jridgewell/gen-mapping, @jridgewell/sourcemap-codec, @jridgewell/trace-mapping | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/jridgewell/sourcemaps.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @jridgewell/resolve-uri | 3.1.2 | MIT / permissive | [upstream](https://github.com/jridgewell/resolve-uri) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @linaria/core | 6.3.0 | MIT / permissive | [upstream](https://github.com/callstack/linaria.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @loaders.gl/3d-tiles, @loaders.gl/compression, @loaders.gl/core, @loaders.gl/crypto, @loaders.gl/csv, @loaders.gl/draco, @loaders.gl/geoarrow, @loaders.gl/gis, @loaders.gl/gltf, @loaders.gl/images, @loaders.gl/loader-utils, @loaders.gl/math, @loaders.gl/mvt, @loaders.gl/schema, @loaders.gl/schema-utils, @loaders.gl/terrain, @loaders.gl/textures, @loaders.gl/tiles, @loaders.gl/wms, @loaders.gl/worker-utils, @loaders.gl/xml, @loaders.gl/zip | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/visgl/loaders.gl) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @luma.gl/core, @luma.gl/engine, @luma.gl/gltf, @luma.gl/gpgpu, @luma.gl/shadertools, @luma.gl/webgl | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/visgl/luma.gl) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/geojson-rewind | 0.5.2 | ISC / permissive | [upstream](https://github.com/mapbox/geojson-rewind.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/geojson-types | 1.0.2 | MIT / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/jsonlint-lines-primitives | 2.0.3 | MIT / permissive | [upstream](https://github.com/mapbox/jsonlint.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/mapbox-gl-supported | 1.5.0 | BSD-3-Clause / permissive | [upstream](https://github.com/mapbox/mapbox-gl-supported.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/martini | 0.2.0 | ISC / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/point-geometry | 0.1.0, 1.1.0 | ISC / permissive | [upstream](https://github.com/mapbox/point-geometry.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/point-geometry | 0.1.0, 1.1.0 | ISC / permissive | [upstream](https://github.com/mapbox/point-geometry.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/tiny-sdf | 1.2.5, 2.2.0 | BSD-2-Clause / permissive | [upstream](https://github.com/mapbox/tiny-sdf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/tiny-sdf | 1.2.5, 2.2.0 | BSD-2-Clause / permissive | [upstream](https://github.com/mapbox/tiny-sdf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/unitbezier | 0.0.0, 1.0.0 | BSD-2-Clause / permissive | [upstream](https://github.com/mapbox/unitbezier.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/vector-tile | 1.3.1, 3.0.0 | BSD-3-Clause / permissive | [upstream](https://github.com/mapbox/vector-tile-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/vector-tile | 1.3.1, 3.0.0 | BSD-3-Clause / permissive | [upstream](https://github.com/mapbox/vector-tile-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mapbox/whoots-js | 3.1.0 | ISC / permissive | [upstream](https://github.com/mapbox/whoots-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @maplibre/geojson-vt | 6.1.1 | MIT / permissive | [upstream](https://github.com/maplibre/geojson-vt) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @maplibre/maplibre-gl-style-spec | 26.4.4 | MIT / permissive | [upstream](https://github.com/maplibre/maplibre-style-spec) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @maplibre/mlt | 1.3.0 | MIT / permissive | [upstream](https://github.com/maplibre/maplibre-tile-spec) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @maplibre/vt-pbf | 4.3.2 | MIT / permissive | [upstream](https://github.com/maplibre/vt-pbf) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @math.gl/core, @math.gl/culling, @math.gl/geospatial, @math.gl/polygon, @math.gl/sun, @math.gl/types, @math.gl/web-mercator | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/visgl/math.gl.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @mermaid-js/parser | 1.2.1 | MIT / permissive | [upstream](https://github.com/mermaid-js/mermaid.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @microlink/react-json-view | 1.31.40 | MIT / permissive | [upstream](https://github.com/microlinkhq/react-json-view.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @plotly/d3 | 3.8.2 | BSD-2-Clause / permissive | [upstream](https://github.com/plotly/d3.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @plotly/d3-sankey, d3-sankey | bundled with Streamlit 1.66.0; upstream notice gives no separate version | BSD-3-Clause / permissive | [upstream](https://github.com/plotly/d3-sankey.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @plotly/d3-sankey-circular | 0.33.1 | MIT / permissive | [upstream](https://github.com/plotly/d3-sankey-circular.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @plotly/point-cluster, regl-error2d, regl-line2d, regl-scatter2d | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/plotly/point-cluster.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @plotly/regl, regl | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/plotly/regl.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @sindresorhus/is, @sindresorhus/slugify, @sindresorhus/transliterate, ansi-regex, ansi-styles, escape-string-regexp, filter-obj, find-up, get-east-asian-width, get-stream, import-fresh, is-plain-obj, locate-path, p-limit, p-locate, parse-json, query-string, split-on-first, string-width, strip-ansi, wrap-ansi, yocto-queue | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/sindresorhus/is.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @streamlit/component-v2-lib | bundled with Streamlit 1.66.0; upstream notice gives no separate version | Apache-2.0 / permissive | [upstream](https://github.com/streamlit/streamlit.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @swc/helpers | 0.5.21 | Apache-2.0 / permissive | [upstream](https://github.com/swc-project/swc.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @turf/area, @turf/boolean-clockwise, @turf/centroid, @turf/clone, @turf/helpers, @turf/invariant, @turf/meta, @turf/rewind | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/Turfjs/turf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @types/brotli, @types/crypto-js, @types/d3, @types/d3-array, @types/d3-axis, @types/d3-brush, @types/d3-chord, @types/d3-color, @types/d3-contour, @types/d3-delaunay, @types/d3-dispatch, @types/d3-drag, @types/d3-dsv, @types/d3-ease, @types/d3-fetch, @types/d3-force, @types/d3-format, @types/d3-geo, @types/d3-hierarchy, @types/d3-interpolate, @types/d3-path, @types/d3-polygon, @types/d3-quadtree, @types/d3-random, @types/d3-scale, @types/d3-scale-chromatic, @types/d3-selection, @types/d3-shape, @types/d3-time, @types/d3-time-format, @types/d3-timer, @types/d3-transition, @types/d3-zoom, @types/debug, @types/estree, @types/estree-jsx, @types/geojson, @types/hammerjs, @types/hast, @types/katex, @types/lodash, @types/mapbox-gl, @types/mdast, @types/ms, @types/node, @types/offscreencanvas, @types/pako, @types/parse-json, @types/prismjs, @types/trusted-types, @types/unist | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/DefinitelyTyped/DefinitelyTyped.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @ungap/structured-clone | 1.3.0 | ISC / permissive | [upstream](https://github.com/ungap/structured-clone.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @upsetjs/venn.js | 2.0.0 | MIT / permissive | [upstream](https://github.com/upsetjs/venn.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @wyw-in-js/processor-utils, @wyw-in-js/shared | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| a5-js | 0.10.0 | Apache-2.0 / permissive | [upstream](https://github.com/felixpalmer/a5.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| acorn | 7.4.1, 8.16.0 | MIT / permissive | [upstream](https://github.com/acornjs/acorn.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ansi-regex, ansi-styles, callsites, is-finite, is-fullwidth-code-point, parent-module, path-exists, path-type, resolve-from, skin-tone, string-width, strip-ansi | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/chalk/ansi-regex.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| apache-arrow | 21.2.0 | Apache-2.0 / permissive | [upstream](https://github.com/apache/arrow-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| argparse | 1.0.10, 2.0.1 | MIT / permissive | [upstream](https://github.com/nodeca/argparse.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| aria-hidden | 1.2.6 | MIT / permissive | [upstream](https://github.com/theKashey/aria-hidden.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| array-find-index, buf-compare, core-assert, deep-strict-equal, is-obj, is-plain-obj, math-log2, number-is-integer, object-assign | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/sindresorhus/array-find-index.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| array-range, mouse-event-offset, parse-unit, webgl-context | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/mattdesl/array-range.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| async-function, async-generator-function | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/ljharb/async-function.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| asynckit | 0.4.0 | MIT / permissive | [upstream](https://github.com/alexindigo/asynckit.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| attr-accept | 4.0.0 | MIT / permissive | [upstream](https://github.com/react-dropzone/attr-accept.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| axios | 1.20.0 | MIT / permissive | [upstream](https://github.com/axios/axios.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| babel-plugin-macros | 3.1.0 | MIT / permissive | [upstream](https://github.com/kentcdodds/babel-plugin-macros) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| bail, ccount, character-entities, character-entities-html4, character-entities-legacy, character-reference-invalid, fault, mdast-util-to-string, unist-util-find-after, unist-util-position, unist-util-visit | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/wooorm/bail.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| balanced-match | 1.0.2, 4.0.4 | MIT / permissive | [upstream](https://github.com/juliangruber/balanced-match.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| base64-arraybuffer | 1.0.2 | MIT / permissive | [upstream](https://github.com/niklasvh/base64-arraybuffer) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| base64-js | 1.5.1 | MIT / permissive | [upstream](https://github.com/beatgammit/base64-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| bidi-js | 1.1.0 | MIT / permissive | [upstream](https://github.com/lojjic/bidi-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| binary-search-bounds | 2.0.5 | MIT / permissive | [upstream](https://github.com/mikolalysenko/binary-search-bounds.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| bit-twiddle, dup, strongly-connected-components, typedarray-pool | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/mikolalysenko/bit-twiddle.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| bl | 2.2.1 | MIT / permissive | [upstream](https://github.com/rvagg/bl.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| brace-expansion, isarray | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/juliangruber/brace-expansion.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| buffer-from | 1.1.2 | MIT / permissive | [upstream](https://github.com/LinusU/buffer-from.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| call-bind-apply-helpers, es-define-property, es-errors, es-object-atoms | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/ljharb/call-bind-apply-helpers.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| canvas-hypertxt | 1.0.3 | MIT / permissive | [upstream](https://github.com/glideapps/canvas-hypertxt.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| char-regex | 1.0.2 | MIT / permissive | [upstream](https://github.com/Richienb/char-regex.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| charenc, crypt | bundled with Streamlit 1.66.0; upstream notice gives no separate version | BSD-3-Clause / permissive | [upstream](https://github.com/pvorb/node-charenc.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| clamp | 1.0.1 | MIT / permissive | [upstream](https://github.com/hughsk/clamp) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| classnames | 2.5.1 | MIT / permissive | [upstream](https://github.com/JedWatson/classnames.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| cliui | 8.0.1, 9.0.1 | ISC / permissive | [upstream](https://github.com/yargs/cliui.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| clsx, escalade | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/lukeed/clsx.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| color | 4.2.3 | MIT / permissive | [upstream](https://github.com/Qix-/color.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| color-convert | 2.0.1 | MIT / permissive | [upstream](https://github.com/Qix-/color-convert.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| color-name | 1.1.4 | MIT / permissive | [upstream](https://github.com/colorjs/color-name.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| color-parse | 1.4.3 | MIT / permissive | [upstream](https://github.com/colorjs/color-parse) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| color-space | 2.0.1 | Unlicense / permissive | [upstream](http://github.com/colorjs/color-space.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| color-string | 1.9.1 | MIT / permissive | [upstream](https://github.com/Qix-/color-string.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| color2k | 2.0.3 | MIT / permissive | [upstream](https://github.com/ricokahler/color2k.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| colorbrewer | 1.5.6 | Apache-2.0 / permissive | [upstream](https://github.com/saikocat/colorbrewer) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| combined-stream, delayed-stream | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/felixge/node-combined-stream.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| comma-separated-tokens, hast-util-is-element, hast-util-parse-selector, hast-util-to-parse5, hast-util-whitespace, html-element-attributes, html-void-elements, is-alphabetical, is-alphanumerical, is-decimal, is-hexadecimal, lowlight, mdast-util-to-hast, rehype-raw, space-separated-tokens, unist-util-remove-position, unist-util-stringify-position, unist-util-visit-parents, vfile-location, web-namespaces, zwitch | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/wooorm/comma-separated-tokens.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| commander | 2.20.3, 7.2.0, 8.3.0 | MIT / permissive | [upstream](https://github.com/tj/commander.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| concat-stream | 1.6.2 | MIT / permissive | [upstream](http://github.com/maxogden/concat-stream.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| convert-source-map | 1.9.0, 2.0.0 | MIT / permissive | [upstream](https://github.com/thlorenz/convert-source-map.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| core-util-is | 1.0.3 | MIT / permissive | [upstream](https://github.com/isaacs/core-util-is) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| cose-base | 1.0.3, 2.2.0 | MIT / permissive | [upstream](https://github.com/iVis-at-Bilkent/cose-base.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| cosmiconfig, tabbable | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/davidtheclark/cosmiconfig.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| country-iso-search | 0.1.2 | MIT / permissive | [upstream](https://github.com/plotly/country-iso-search.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| css-font | 1.2.0 | MIT / permissive | [upstream](https://github.com/dy/css-font.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| css-font-size-keywords, css-font-stretch-keywords, css-font-style-keywords, css-font-weight-keywords, css-global-keywords, css-system-font-keywords | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/jedmao/css-font-size-keywords.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| csstype | 3.2.3 | MIT / permissive | [upstream](https://github.com/frenic/csstype) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| culori | 4.0.2 | MIT / permissive | [upstream](https://github.com/Evercoder/culori.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| cytoscape | 3.34.1 | MIT / permissive | [upstream](https://github.com/cytoscape/cytoscape.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| cytoscape-cose-bilkent | 4.1.0 | MIT / permissive | [upstream](https://github.com/cytoscape/cytoscape.js-cose-bilkent.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| cytoscape-fcose | 2.2.0 | MIT / permissive | [upstream](https://github.com/iVis-at-Bilkent/cytoscape.js-fcose.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d, es6-symbol, esniff | bundled with Streamlit 1.66.0; upstream notice gives no separate version | ISC / permissive | [upstream](https://github.com/medikoo/d.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3, d3-array | bundled with Streamlit 1.66.0; upstream notice gives no separate version | ISC / permissive | [upstream](https://github.com/d3/d3.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-array, d3-dispatch, d3-force, d3-hierarchy, d3-quadtree, d3-time, d3-timer | bundled with Streamlit 1.66.0; upstream notice gives no separate version | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-array.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-array | 1.2.4, 2.12.1, 3.2.4 | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-array.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-axis, d3-brush, d3-chord, d3-dispatch, d3-drag, d3-force, d3-hierarchy, d3-interpolate, d3-polygon, d3-quadtree, d3-random, d3-scale, d3-selection, d3-time-format, d3-timer, d3-transition, d3-zoom | bundled with Streamlit 1.66.0; upstream notice gives no separate version | ISC / permissive | [upstream](https://github.com/d3/d3-axis.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-collection | 1.0.7 | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-collection.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-color, d3-shape, d3-time | bundled with Streamlit 1.66.0; upstream notice gives no separate version | ISC / permissive | [upstream](https://github.com/d3/d3-color.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-contour | 4.0.2 | ISC / permissive | [upstream](https://github.com/d3/d3-contour.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-delaunay | 6.0.4 | ISC / permissive | [upstream](https://github.com/d3/d3-delaunay.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-dsv | 1.2.0, 3.0.1 | ISC / permissive | [upstream](https://github.com/d3/d3-dsv.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-dsv | 1.2.0, 3.0.1 | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-dsv.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-ease | 3.0.1 | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-ease.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-fetch | 3.0.1 | ISC / permissive | [upstream](https://github.com/d3/d3-fetch.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-format | 1.4.5, 3.1.2 | ISC / permissive | [upstream](https://github.com/d3/d3-format.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-format, d3-shape | bundled with Streamlit 1.66.0; upstream notice gives no separate version | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-format.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-geo | 1.12.1, 3.1.1 | MIT / permissive | [upstream](https://github.com/d3/d3-geo.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-geo | 1.12.1, 3.1.1 | MIT / permissive | [upstream](https://github.com/d3/d3-geo.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-geo-projection | 2.9.0, 4.0.0 | MIT / permissive | [upstream](https://github.com/d3/d3-geo-projection.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-geo-projection | 2.9.0, 4.0.0 | MIT / permissive | [upstream](https://github.com/d3/d3-geo-projection.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-graphviz | 5.6.0 | BSD-3-Clause / permissive | [upstream](https://github.com/magjac/d3-graphviz.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-hexbin | 0.2.2 | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-hexbin.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-path | 1.0.9, 3.1.0 | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-path.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-path | 1.0.9, 3.1.0 | ISC / permissive | [upstream](https://github.com/d3/d3-path.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-scale-chromatic | 3.1.0 | Apache-2.0 / permissive | [upstream](https://github.com/d3/d3-scale-chromatic.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| d3-time-format | 2.3.0, 4.1.0 | BSD-3-Clause / permissive | [upstream](https://github.com/d3/d3-time-format.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| dagre-d3-es | 7.0.14 | MIT / permissive | [upstream](https://github.com/tbo47/dagre-es.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| dayjs | 1.11.23 | MIT / permissive | [upstream](https://github.com/iamkun/dayjs.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| debug | 2.6.9, 3.2.7, 4.4.3 | MIT / permissive | [upstream](https://github.com/visionmedia/debug.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| decode-named-character-reference, micromark-extension-gfm-footnote | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/wooorm/decode-named-character-reference.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| decode-uri-component | 0.5.0 | MIT / permissive | [upstream](https://github.com/SamVerschueren/decode-uri-component.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| defined, minimist, resolve, shallow-copy | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/inspect-js/defined.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| delaunator, supercluster | bundled with Streamlit 1.66.0; upstream notice gives no separate version | ISC / permissive | [upstream](https://github.com/mapbox/delaunator.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| dequal | 2.0.3 | MIT / permissive | [upstream](https://github.com/lukeed/dequal.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| devlop | 1.1.0 | MIT / permissive | [upstream](https://github.com/wooorm/devlop.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| dom-helpers | 5.2.1 | MIT / permissive | [upstream](https://github.com/react-bootstrap/dom-helpers.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| dunder-proto, math-intrinsics | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/es-shims/dunder-proto.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| duplexify, end-of-stream, protocol-buffers-schema | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/mafintosh/duplexify) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| earcut | 2.2.4, 3.2.3 | ISC / permissive | [upstream](https://github.com/mapbox/earcut.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| earcut | 2.2.4, 3.2.3 | ISC / permissive | [upstream](https://github.com/mapbox/earcut.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| echarts | 6.1.0 | Apache-2.0 / permissive | [upstream](https://github.com/apache/echarts.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| elementary-circuits-directed-graph | 1.3.1 | MIT / permissive | [upstream](https://github.com/antoinerg/elementary-circuits-directed-graph.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| emojilib | 2.4.0 | MIT / permissive | [upstream](https://github.com/muan/emojilib.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| emoticon, markdown-table | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/wooorm/emoticon.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| entities | 4.5.0 | BSD-2-Clause / permissive | [upstream](https://github.com/fb55/entities.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| error-ex, is-arrayish | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/qix-/node-error-ex.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| es-set-tostringtag | 2.1.0 | MIT / permissive | [upstream](https://github.com/es-shims/es-set-tostringtag.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| es-toolkit | 1.46.1 | MIT / permissive | [upstream](https://github.com/toss/es-toolkit.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| es5-ext | 0.10.64 | ISC / permissive | [upstream](https://github.com/medikoo/es5-ext.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| es6-iterator | 2.0.3 | MIT / permissive | [upstream](https://github.com/medikoo/es6-iterator.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| es6-weak-map | 2.0.3 | ISC / permissive | [upstream](https://github.com/medikoo/es6-weak-map.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| escodegen | 2.1.0 | BSD-2-Clause / permissive | [upstream](http://github.com/estools/escodegen.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| esprima | 4.0.1 | BSD-2-Clause / permissive | [upstream](https://github.com/jquery/esprima.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| estraverse, esutils | bundled with Streamlit 1.66.0; upstream notice gives no separate version | BSD-2-Clause / permissive | [upstream](http://github.com/estools/estraverse.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| estree-util-is-identifier-name, mdast-util-gfm-autolink-literal, mdast-util-gfm-strikethrough, mdast-util-gfm-table, mdast-util-gfm-task-list-item, mdast-util-math, mdast-util-mdx-expression, mdast-util-mdx-jsx, mdast-util-mdxjs-esm, micromark-extension-gfm, micromark-extension-gfm-autolink-literal, micromark-extension-gfm-strikethrough, micromark-extension-gfm-tagfilter, micromark-extension-gfm-task-list-item, micromark-extension-math | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/syntax-tree/estree-util-is-identifier-name.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| event-emitter | 0.3.5 | MIT / permissive | [upstream](https://github.com/medikoo/event-emitter.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| events | 3.3.0 | MIT / permissive | [upstream](https://github.com/Gozala/events.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ext | 1.7.0 | ISC / permissive | [upstream](https://github.com/medikoo/es5-ext#ext) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| extend | 3.0.2 | MIT / permissive | [upstream](https://github.com/justmoon/node-extend.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| falafel, resolve | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/substack/node-falafel.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| fast-isnumeric | 1.1.4 | MIT / permissive | [upstream](https://github.com/plotly/fast-isnumeric.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| fast-json-patch | 3.1.1 | MIT / permissive | [upstream](https://github.com/Starcounter-Jack/JSON-Patch.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| fast-xml-builder | 1.1.9 | MIT / permissive | [upstream](https://github.com/NaturalIntelligence/fast-xml-builder.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| fast-xml-parser | 5.7.1 | MIT / permissive | [upstream](https://github.com/NaturalIntelligence/fast-xml-parser.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| fetch-blob | 3.2.0 | MIT / permissive | [upstream](https://github.com/node-fetch/fetch-blob.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| fflate | 0.7.5 | MIT / permissive | [upstream](https://github.com/101arrowz/fflate) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| file-selector | 5.0.1 | MIT / permissive | [upstream](https://github.com/react-dropzone/file-selector.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| find-root | 1.1.0 | MIT / permissive | [upstream](https://github.com/js-n/find-root.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| flatten-vertex-data | 1.0.2 | MIT / permissive | [upstream](https://github.com/glo-js/flatten-vertex-data.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| follow-redirects | 1.16.0 | MIT / permissive | [upstream](https://github.com/follow-redirects/follow-redirects.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| font-atlas | 2.1.0 | MIT / permissive | [upstream](https://github.com/hughsk/font-atlas.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| form-data | 4.0.6 | MIT / permissive | [upstream](https://github.com/form-data/form-data.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| from2, glsl-resolve, map-limit | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/hughsk/from2) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| function-bind | 1.1.2 | MIT / permissive | [upstream](https://github.com/Raynos/function-bind.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| generator-function | 2.0.1 | MIT / permissive | [upstream](https://github.com/TimothyGu/generator-function.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| geojson-vt | 3.2.1 | ISC / permissive | [upstream](https://github.com/mapbox/geojson-vt.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| get-caller-file | 2.0.5 | ISC / permissive | [upstream](https://github.com/stefanpenner/get-caller-file.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| get-canvas-context, glsl-token-inject-block | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/Jam3/get-canvas-context.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| get-intrinsic | 1.3.1 | MIT / permissive | [upstream](https://github.com/ljharb/get-intrinsic.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| get-proto | 1.0.1 | MIT / permissive | [upstream](https://github.com/ljharb/get-proto.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| gl-mat4 | 1.2.0 | Zlib / permissive | [upstream](https://github.com/stackgl/gl-mat4) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| gl-matrix | 3.4.4 | MIT / permissive | [upstream](https://github.com/toji/gl-matrix.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| gl-text, regl-splom | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/a-vis/gl-text.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| glsl-inject-defines, glsl-token-assignments, glsl-token-defines, glsl-token-depth, glsl-token-descope, glsl-token-properties, glsl-token-scope, glsl-token-string | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/mattdesl/glsl-inject-defines.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| glsl-token-whitespace-trim | 1.0.0 | MIT / permissive | [upstream](https://github.com/hughsk/glsl-token-whitespace-trim.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| glsl-tokenizer | 2.1.5 | MIT / permissive | [upstream](https://github.com/gl-modules/glsl-tokenizer.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| glslify | 7.1.1 | MIT / permissive | [upstream](https://github.com/stackgl/glslify.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| glslify-bundle | 5.1.1 | MIT / permissive | [upstream](https://github.com/stackgl/glslify-bundle.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| gopd | 1.2.0 | MIT / permissive | [upstream](https://github.com/ljharb/gopd.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| graceful-fs | 4.2.11 | ISC / permissive | [upstream](https://github.com/isaacs/node-graceful-fs) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| grid-index | 1.1.0 | ISC / permissive | [upstream](https://github.com/mapbox/grid-index.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| h3-js | 4.4.0 | Apache-2.0 / permissive | [upstream](https://github.com/uber/h3-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hachure-fill | 0.5.2 | MIT / permissive | [upstream](https://github.com/pshihn/hachure-fill.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hammerjs | 2.0.8 | MIT / permissive | [upstream](https://github.com/hammerjs/hammer.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| has-passive-events, parse-rect, to-float32 | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/dfcreative/has-passive-events.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| has-symbols | 1.1.0 | MIT / permissive | [upstream](https://github.com/inspect-js/has-symbols.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| has-tostringtag | 1.0.2 | MIT / permissive | [upstream](https://github.com/inspect-js/has-tostringtag.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hasown | 2.0.4 | MIT / permissive | [upstream](https://github.com/inspect-js/hasOwn.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hast-util-from-dom | 5.0.1 | ISC / permissive | [upstream](https://github.com/syntax-tree/hast-util-from-dom.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hast-util-from-html | 2.0.3 | MIT / permissive | [upstream](https://github.com/syntax-tree/hast-util-from-html.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hast-util-from-html-isomorphic | 2.0.0 | MIT / permissive | [upstream](https://github.com/syntax-tree/hast-util-from-html-isomorphic.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hast-util-from-parse5, hast-util-raw, hast-util-to-jsx-runtime, hastscript, mdast-util-directive, mdast-util-find-and-replace, mdast-util-from-markdown, mdast-util-gfm, mdast-util-gfm-footnote, mdast-util-to-markdown, micromark, micromark-core-commonmark, micromark-extension-directive, micromark-extension-gfm-table, micromark-factory-destination, micromark-factory-label, micromark-factory-space, micromark-factory-title, micromark-factory-whitespace, micromark-util-character, micromark-util-chunked, micromark-util-classify-character, micromark-util-combine-extensions, micromark-util-decode-numeric-character-reference, micromark-util-decode-string, micromark-util-encode, micromark-util-html-tag-name, micromark-util-normalize-identifier, micromark-util-resolve-all, micromark-util-sanitize-uri, micromark-util-subtokenize, micromark-util-symbol, micromark-util-types, remark-directive, remark-gfm, remark-rehype | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/syntax-tree/hast-util-from-parse5.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hast-util-to-text | 4.0.2 | MIT / permissive | [upstream](https://github.com/syntax-tree/hast-util-to-text.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| highlight.js | 10.7.3 | BSD-3-Clause / permissive | [upstream](https://github.com/highlightjs/highlight.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hoist-non-react-statics | 3.3.2 | BSD-3-Clause / permissive | [upstream](https://github.com/mridgway/hoist-non-react-statics.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| hotkeys-js | 4.0.8 | MIT / permissive | [upstream](https://github.com/jaywcjlove/hotkeys-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| html-url-attributes | 3.0.1 | MIT / permissive | [upstream](https://github.com/rehypejs/rehype-minify/tree/main/packages/html-url-attributes) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| iconv-lite | 0.4.24, 0.6.3 | MIT / permissive | [upstream](https://github.com/ashtuchkin/iconv-lite.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ieee754 | 1.2.1 | BSD-3-Clause / permissive | [upstream](https://github.com/feross/ieee754.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| iframe-resizer | 4.3.11 | MIT / permissive | [upstream](https://github.com/davidjbradshaw/iframe-resizer.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| image-size | 2.0.4 | MIT / permissive | [upstream](https://codeberg.org/image-size/image-size.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| immediate | 3.0.6 | MIT / permissive | [upstream](https://github.com/calvinmetcalf/immediate.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| immer | 11.1.21 | MIT / permissive | [upstream](https://github.com/immerjs/immer.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| import-meta-resolve | 4.2.0 | MIT / permissive | [upstream](https://github.com/wooorm/import-meta-resolve.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| inherits | 2.0.4 | ISC / permissive | [upstream](https://github.com/isaacs/inherits) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| inline-style-parser | 0.2.4 | MIT / permissive | [upstream](https://github.com/remarkablemark/inline-style-parser) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| internmap | 1.0.1, 2.0.3 | ISC / permissive | [upstream](https://github.com/mbostock/internmap.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| invariant, prop-types | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/zertosh/invariant) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| is-browser | 2.1.0 | MIT / permissive | [upstream](https://github.com/ForbesLindesay/is-browser.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| is-buffer, safe-buffer | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/feross/is-buffer.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| is-core-module | 2.16.1 | MIT / permissive | [upstream](https://github.com/inspect-js/is-core-module.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| is-error | 2.2.2 | MIT / permissive | [upstream](https://github.com/mk-pmb/is-error-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| is-firefox | 1.0.3 | MIT / permissive | [upstream](https://github.com/gillstrom/is-firefox.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| is-string-blank | 1.0.1 | MIT / permissive | [upstream](https://github.com/plotly/is-string-blank.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| js-tokens | 10.0.0, 4.0.0 | MIT / permissive | [upstream](https://github.com/lydell/js-tokens.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| jsep | 0.3.5, 1.4.0 | MIT / permissive | [upstream](https://github.com/EricSmekens/jsep.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| json-parse-even-better-errors | 2.3.1 | MIT / permissive | [upstream](https://github.com/npm/json-parse-even-better-errors) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| json-stringify-pretty-compact | 4.0.0 | MIT / permissive | [upstream](https://github.com/lydell/json-stringify-pretty-compact.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| json-with-bigint | 3.5.10 | MIT / permissive | [upstream](https://github.com/Ivan-Korolenko/json-with-bigint) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| json5 | 2.2.3 | MIT / permissive | [upstream](https://github.com/json5/json5.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| jszip | 3.10.1 | MIT (selected; also offered under GPL-3.0) / permissive | [upstream](https://github.com/Stuk/jszip.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| katex | 0.16.47 | MIT / permissive | [upstream](https://github.com/KaTeX/KaTeX.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| kdbush, quickselect | bundled with Streamlit 1.66.0; upstream notice gives no separate version | ISC / permissive | [upstream](https://github.com/mourner/kdbush.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| kdbush | 3.0.0, 4.1.0 | ISC / permissive | [upstream](https://github.com/mourner/kdbush.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| khroma | 2.1.0 | MIT / permissive | [upstream](https://github.com/fabiospampinato/khroma.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ktx-parse | 0.7.1 | MIT / permissive | [upstream](https://github.com/donmccurdy/ktx-parse.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| layout-base | 1.0.2, 2.0.1 | MIT / permissive | [upstream](https://github.com/iVis-at-Bilkent/layout-base.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| lie | 3.3.0 | MIT / permissive | [upstream](https://github.com/calvinmetcalf/lie.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| lines-and-columns | 1.2.4 | MIT / permissive | [upstream](https://github.com/eventualbuddha/lines-and-columns.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| lodash, lodash-es, lodash.merge | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/lodash/lodash.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| long | 3.2.0, 5.3.2 | Apache-2.0 / permissive | [upstream](https://github.com/dcodeIO/long.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| longest-streak, parse-entities, property-information, stringify-entities, trim-lines | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/wooorm/longest-streak.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| loose-envify | 1.4.0 | MIT / permissive | [upstream](https://github.com/zertosh/loose-envify.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| mapbox-gl | 1.13.3 | MIT / permissive | [upstream](https://github.com/mapbox/mapbox-gl-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| maplibre-gl | 6.11.2 | MIT / permissive | [upstream](https://github.com/maplibre/maplibre-gl-js) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| marked | 16.4.2, 18.1.0, 4.3.0 | MIT / permissive | [upstream](https://github.com/markedjs/marked.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| material-colors | 1.2.6 | ISC / permissive | [upstream](https://github.com/shuhei/material-colors.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| md5 | 2.3.0 | BSD-3-Clause / permissive | [upstream](https://github.com/pvorb/node-md5.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| mdast-util-phrasing | 4.1.0 | MIT / permissive | [upstream](https://github.com/syntax-tree/mdast-util-phrasing.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| memoize-one | 6.0.0 | MIT / permissive | [upstream](https://github.com/alexreardon/memoize-one.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| mermaid | 11.17.2 | MIT / permissive | [upstream](https://github.com/mermaid-js/mermaid) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| meshoptimizer | 1.2.0 | MIT / permissive | [upstream](https://github.com/zeux/meshoptimizer) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| mime-db | 1.52.0 | MIT / permissive | [upstream](https://github.com/jshttp/mime-db.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| mime-types | 2.1.35 | MIT / permissive | [upstream](https://github.com/jshttp/mime-types.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| minimatch | 10.2.6, 5.1.9, 9.0.9 | ISC / permissive | [upstream](https://github.com/isaacs/minimatch.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| mjolnir.js | 2.7.3, 3.1.1 | MIT / permissive | [upstream](https://github.com/visgl/mjolnir.js) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| moment | 2.31.0 | MIT / permissive | [upstream](https://github.com/moment/moment.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| moment-duration-format | 2.3.2 | MIT / permissive | [upstream](https://github.com/jsmreese/moment-duration-format.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| moment-timezone | 0.6.5 | MIT / permissive | [upstream](https://github.com/moment/moment-timezone.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ms | 2.0.0, 2.1.3 | MIT / permissive | [upstream](https://github.com/zeit/ms.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ms | 2.0.0, 2.1.3 | MIT / permissive | [upstream](https://github.com/vercel/ms.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| native-file-system-adapter | 3.0.1 | MIT / permissive | [upstream](https://github.com/jimmywarting/native-file-system-adapter.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| needle | 2.9.1 | MIT / permissive | [upstream](https://github.com/tomas/needle.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| next-tick | 1.1.0 | ISC / permissive | [upstream](https://github.com/medikoo/next-tick.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| node-domexception | 1.0.0 | MIT / permissive | [upstream](https://github.com/jimmywarting/node-domexception.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| node-emoji | 2.2.0 | MIT / permissive | [upstream](https://github.com/omnidan/node-emoji) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| normalize-svg-path | 1.1.0 | MIT / permissive | [upstream](https://github.com/jkroso/normalize-svg-path.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| numbro | 2.5.0 | MIT / permissive | [upstream](https://github.com/BenjaminVanRyseghem/numbro) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| once, semver, wrappy | bundled with Streamlit 1.66.0; upstream notice gives no separate version | ISC / permissive | [upstream](https://github.com/isaacs/once) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| orderedmap, w3c-keyname | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/marijnh/orderedmap.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| package-manager-detector | 1.8.0 | MIT / permissive | [upstream](https://github.com/antfu-collective/package-manager-detector.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| pako | 1.0.11 | MIT / permissive | [upstream](https://github.com/nodeca/pako.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| parenthesis | 3.1.8 | MIT / permissive | [upstream](https://github.com/dy/parenthesis.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| parse-svg-path | 0.1.2, 0.2.0 | MIT / permissive | [upstream](https://github.com/jkroso/parse-svg-path.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| parse5 | 7.1.2 | MIT / permissive | [upstream](https://github.com/inikulin/parse5.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| path-data-parser, points-on-curve | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/pshihn/path-data-parser.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| path-expression-matcher | 1.5.0 | MIT / permissive | [upstream](https://github.com/NaturalIntelligence/path-expression-matcher) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| path-parse | 1.0.7 | MIT / permissive | [upstream](https://github.com/jbgutierrez/path-parse.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| pbf | 3.3.0, 5.1.2 | BSD-3-Clause / permissive | [upstream](https://github.com/mapbox/pbf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| pbf | 3.3.0, 5.1.2 | BSD-3-Clause / permissive | [upstream](https://github.com/mapbox/pbf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| performance-now | 2.1.0 | MIT / permissive | [upstream](https://github.com/braveg1rl/performance-now.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| picocolors | 1.1.1 | ISC / permissive | [upstream](https://github.com/alexeyraspopov/picocolors.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| plotly.js | 4.1.2 | MIT / permissive | [upstream](https://github.com/plotly/plotly.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| point-in-polygon | 1.1.0 | MIT / permissive | [upstream](https://github.com/substack/point-in-polygon.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| points-on-path | 0.2.1 | MIT / permissive | [upstream](https://github.com/pshihn/points-on-path.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| polybooljs | 1.2.2 | MIT / permissive | [upstream](https://github.com/velipso/polybooljs) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| potpack | 1.0.2, 2.1.0 | ISC / permissive | [upstream](https://github.com/mapbox/potpack.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| potpack | 1.0.2, 2.1.0 | ISC / permissive | [upstream](https://github.com/mapbox/potpack.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| preact | 10.29.8 | MIT / permissive | [upstream](https://github.com/preactjs/preact.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| prismjs | 1.30.0 | MIT / permissive | [upstream](https://github.com/PrismJS/prism.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| probe-image-size | 7.4.0 | MIT / permissive | [upstream](https://github.com/nodeca/probe-image-size.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| process-nextick-args | 2.0.1 | MIT / permissive | [upstream](https://github.com/calvinmetcalf/process-nextick-args.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| property-information | 6.5.0, 7.1.0 | MIT / permissive | [upstream](https://github.com/wooorm/property-information.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| prosemirror-commands, prosemirror-history, prosemirror-inputrules, prosemirror-keymap, prosemirror-model, prosemirror-state, prosemirror-transform, prosemirror-view | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/prosemirror/prosemirror-commands.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| protobufjs | 8.8.0 | BSD-3-Clause / permissive | [upstream](https://github.com/protobufjs/protobuf.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| proxy-from-env | 2.1.0 | MIT / permissive | [upstream](https://github.com/Rob--W/proxy-from-env.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| quickselect | 2.0.0, 3.0.0 | ISC / permissive | [upstream](https://github.com/mourner/quickselect.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| raf | 3.4.1 | MIT / permissive | [upstream](https://github.com/chrisdickinson/raf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| rc-overflow, rc-resize-observer | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/react-component/overflow.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| rc-util | 5.44.4 | MIT / permissive | [upstream](https://github.com/react-component/util.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| re-resizable | 6.11.2 | MIT / permissive | [upstream](https://github.com/bokuweb/react-resizable-box.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react, react-dom, react-is, scheduler | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/facebook/react.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-base16-styling | 0.10.0 | MIT / permissive | [upstream](https://github.com/reduxjs/redux-devtools.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-color, reactcss | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/casesandberg/react-color.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-dropzone | 20.1.2 | MIT / permissive | [upstream](https://github.com/react-dropzone/react-dropzone.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-fast-compare | 3.2.2 | MIT / permissive | [upstream](https://github.com/FormidableLabs/react-fast-compare) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-feather | 2.0.10 | MIT / permissive | [upstream](https://github.com/feathericons/react-feather.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-helmet-async | 3.0.0 | Apache-2.0 / permissive | [upstream](http://github.com/staylor/react-helmet-async) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-html-attributes | 1.4.6 | MIT / permissive | [upstream](https://github.com/jackyho112/react-html-attributes) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-lifecycles-compat | 3.0.4 | MIT / permissive | [upstream](https://github.com/reactjs/react-lifecycles-compat.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-map-gl | 5.3.21 | MIT / permissive | [upstream](https://github.com/visgl/react-map-gl.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-markdown | 10.1.0 | MIT / permissive | [upstream](https://github.com/remarkjs/react-markdown.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-plotly.js | 4.1.0 | MIT / permissive | [upstream](https://github.com/plotly/react-plotly.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-responsive-carousel | 3.2.23 | MIT / permissive | [upstream](https://github.com/leandrowd/react-responsive-carousel.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-select | 5.10.2 | MIT / permissive | [upstream](https://github.com/JedWatson/react-select/tree/master/packages/react-select) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-syntax-highlighter | 16.1.1 | MIT / permissive | [upstream](https://github.com/react-syntax-highlighter/react-syntax-highlighter.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-textarea-autosize | 8.5.9 | MIT / permissive | [upstream](https://github.com/Andarist/react-textarea-autosize.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-transition-group | 4.4.5 | BSD-3-Clause / permissive | [upstream](https://github.com/reactjs/react-transition-group.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-webcam | 7.2.0 | MIT / permissive | [upstream](https://github.com/mozmorris/react-webcam.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| readable-stream | 1.0.34, 2.3.8 | MIT / permissive | [upstream](https://github.com/isaacs/readable-stream) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| readable-stream | 1.0.34, 2.3.8 | MIT / permissive | [upstream](https://github.com/nodejs/readable-stream) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| refractor | 5.0.0 | MIT / permissive | [upstream](https://github.com/wooorm/refractor.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| remark-emoji | 5.0.2 | MIT / permissive | [upstream](https://github.com/rhysd/remark-emoji.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| remark-parse, remark-stringify | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/remarkjs/remark/tree/main/packages/remark-parse) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| remend | 1.4.0 | Apache-2.0 / permissive | [upstream](https://github.com/vercel/streamdown.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| require-directory | 2.1.1 | MIT / permissive | [upstream](https://github.com/troygoode/node-require-directory.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| require-from-string | 2.0.2 | MIT / permissive | [upstream](https://github.com/floatdrop/require-from-string.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| resize-observer-polyfill | 1.5.1 | MIT / permissive | [upstream](https://github.com/que-etc/resize-observer-polyfill.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| resolve-protobuf-schema | 2.1.0 | MIT / permissive | [upstream](https://github.com/mafintosh/resolve-protobuf-schema.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| robust-predicates | 3.0.2 | Unlicense / permissive | [upstream](https://github.com/mourner/robust-predicates.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| rope-sequence | 1.3.4 | MIT / permissive | [upstream](https://github.com/marijnh/rope-sequence.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| roughjs | 4.6.6 | MIT / permissive | [upstream](https://github.com/pshihn/rough.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| rw | 1.3.3 | BSD-2-Clause / permissive | [upstream](http://github.com/mbostock/rw.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| safer-buffer | 2.1.2 | MIT / permissive | [upstream](https://github.com/ChALkeR/safer-buffer.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| sax | 1.4.1 | MIT / permissive | [upstream](https://github.com/isaacs/sax-js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| setimmediate | 1.0.5 | MIT / permissive | [upstream](https://github.com/YuzuJS/setImmediate.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| shallowequal | 1.1.0 | MIT / permissive | [upstream](https://github.com/dashed/shallowequal.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| simple-swizzle | 0.2.4 | MIT / permissive | [upstream](https://github.com/qix-/node-simple-swizzle.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| snappyjs | 0.6.1 | MIT / permissive | [upstream](https://github.com/zhipeng-jia/snappyjs.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| source-map | 0.5.7, 0.6.1 | BSD-3-Clause / permissive | [upstream](http://github.com/mozilla/source-map.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| sprintf-js | 1.0.3 | BSD-3-Clause / permissive | [upstream](https://github.com/alexei/sprintf.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| stack-trace | 0.0.9 | MIT / permissive | [upstream](https://github.com/felixge/node-stack-trace.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| static-eval | 2.1.1 | MIT / permissive | [upstream](https://github.com/browserify/static-eval.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| stream-parser | 0.3.1 | MIT / permissive | [upstream](https://github.com/TooTallNate/node-stream-parser.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| stream-shift | 1.0.3 | MIT / permissive | [upstream](https://github.com/mafintosh/stream-shift.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| string_decoder | 0.10.31, 1.1.1 | MIT / permissive | [upstream](https://github.com/rvagg/string_decoder.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| string_decoder | 0.10.31, 1.1.1 | MIT / permissive | [upstream](https://github.com/nodejs/string_decoder.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| strnum | 2.2.3 | MIT / permissive | [upstream](https://github.com/NaturalIntelligence/strnum) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| style-to-js | 1.1.16 | MIT / permissive | [upstream](https://github.com/remarkablemark/style-to-js) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| style-to-object | 1.0.8 | MIT / permissive | [upstream](https://github.com/remarkablemark/style-to-object) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| stylis | 4.2.0, 4.4.0 | MIT / permissive | [upstream](https://github.com/thysultan/stylis.js) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| supports-preserve-symlinks-flag | 1.0.0 | MIT / permissive | [upstream](https://github.com/inspect-js/node-supports-preserve-symlinks-flag.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| svg-arc-to-cubic-bezier | 3.2.0 | ISC / permissive | [upstream](https://github.com/colinmeinke/svg-arc-to-cubic-bezier) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| svg-path-sdf | 2.0.0 | MIT / permissive | [upstream](https://github.com/dy/svg-path-sdf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| texture-compressor | 1.0.2 | MIT / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| through2 | 0.6.5, 2.0.5 | MIT / permissive | [upstream](https://github.com/rvagg/through2.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| through2 | 0.6.5, 2.0.5 | MIT / permissive | [upstream](https://github.com/rvagg/through2.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| tinycolor2 | 1.6.0 | MIT / permissive | [upstream](https://github.com/bgrins/TinyColor.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| tinyexec | 1.3.1 | MIT / permissive | [upstream](https://github.com/tinylibs/tinyexec.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| tinyqueue | 2.0.3, 3.0.0 | ISC / permissive | [upstream](https://github.com/mourner/tinyqueue.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| to-px | 1.1.0 | MIT / permissive | [upstream](https://github.com/mikolalysenko/to-px.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| topojson-client | 3.1.0 | ISC / permissive | [upstream](https://github.com/topojson/topojson-client.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| trough | 2.2.0 | MIT / permissive | [upstream](https://github.com/wooorm/trough.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ts-dedent | 2.2.0 | MIT / permissive | [upstream](https://github.com/tamino-martinius/node-ts-dedent.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| ts-invariant | 0.10.3 | MIT / permissive | [upstream](https://github.com/apollographql/invariant-packages.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| tslib | 2.3.0, 2.8.1 | ISC / permissive | [upstream](https://github.com/Microsoft/tslib.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| type | 2.7.3 | ISC / permissive | [upstream](https://github.com/medikoo/type.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| typed-signals | 3.0.0 | CC0-1.0 / permissive | [upstream](https://github.com/Lusito/typed-signals.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| typedarray | 0.0.6 | MIT / permissive | [upstream](https://github.com/substack/typedarray.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| undici-types | 7.24.6 | MIT / permissive | [upstream](https://github.com/nodejs/undici.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| unified, vfile | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/unifiedjs/unified.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| unist-util-is | 6.0.0 | MIT / permissive | [upstream](https://github.com/syntax-tree/unist-util-is.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| unquote | 1.1.1 | MIT / permissive | [upstream](https://github.com/lakenen/node-unquote.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| urlpattern-polyfill | 10.1.0 | MIT / permissive | [upstream](https://github.com/kenchris/urlpattern-polyfill) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| util-deprecate | 1.0.2 | MIT / permissive | [upstream](https://github.com/TooTallNate/util-deprecate.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| uuid | 14.0.2 | MIT / permissive | [upstream](https://github.com/uuidjs/uuid.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vega, vega-canvas, vega-crossfilter, vega-dataflow, vega-encode, vega-event-selector, vega-expression, vega-force, vega-format, vega-functions, vega-geo, vega-hierarchy, vega-interpreter, vega-label, vega-loader, vega-parser, vega-projection, vega-regression, vega-runtime, vega-scale, vega-scenegraph, vega-selections, vega-statistics, vega-time, vega-transforms, vega-typings, vega-util, vega-view, vega-view-transforms, vega-voronoi, vega-wordcloud | bundled with Streamlit 1.66.0; upstream notice gives no separate version | BSD-3-Clause / permissive | [upstream](https://github.com/vega/vega.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vega-embed | 7.3.0 | BSD-3-Clause / permissive | [upstream](https://github.com/vega/vega-embed.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vega-lite | 6.4.3 | BSD-3-Clause / permissive | [upstream](https://github.com/vega/vega-lite.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vega-schema-url-parser | 3.0.2 | BSD-3-Clause / permissive | [upstream](https://github.com/vega/schema.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vega-themes | 3.0.0 | BSD-3-Clause / permissive | [upstream](https://github.com/vega/vega-themes.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vega-tooltip | 1.1.0 | BSD-3-Clause / permissive | [upstream](https://github.com/vega/vega-tooltip.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vfile-message | 4.0.2 | MIT / permissive | [upstream](https://github.com/vfile/vfile-message.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| vt-pbf | 3.1.3 | MIT / permissive | [upstream](https://github.com/mapbox/vt-pbf.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| wavesurfer.js | 8.0.2 | BSD-3-Clause / permissive | [upstream](https://github.com/katspaugh/wavesurfer.js.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| web-streams-polyfill | 3.3.3 | MIT / permissive | [upstream](https://github.com/MattiasBuelens/web-streams-polyfill.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| world-calendars | 1.0.4 | MIT / permissive | [upstream](https://github.com/plotly/world-calendars.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| xtend | 2.2.0, 4.0.2 | MIT / permissive | [upstream](https://github.com/Raynos/xtend.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| xxhashjs | 0.2.2 | MIT / permissive | [upstream](https://github.com/pierrec/js-xxhash) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| y18n | 5.0.8 | ISC / permissive | [upstream](https://github.com/yargs/y18n.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| yaml | 1.10.3, 2.9.1 | ISC / permissive | [upstream](https://github.com/eemeli/yaml.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| yargs | 17.7.2, 18.0.0, 18.1.0 | MIT / permissive | [upstream](https://github.com/yargs/yargs.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| yargs-parser | 21.1.1, 22.0.0 | ISC / permissive | [upstream](https://github.com/yargs/yargs-parser.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| zrender | 6.1.0 | BSD-3-Clause / permissive | [upstream](https://github.com/ecomfe/zrender.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| @linaria/react | 6.3.0 | MIT / permissive | [upstream](https://github.com/callstack/linaria.git) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react-number-format | 5.4.4 | MIT / permissive | [upstream](https://github.com/s-yadav/react-number-format) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| Source Code | bundled with Streamlit 1.66.0; upstream notice gives no separate version | OFL-1.1 / weak copyleft (font only) | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| Source Sans | bundled with Streamlit 1.66.0; upstream notice gives no separate version | OFL-1.1 / weak copyleft (font only) | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| Source Serif | bundled with Streamlit 1.66.0; upstream notice gives no separate version | OFL-1.1 / weak copyleft (font only) | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| Material Icons | bundled with Streamlit 1.66.0; upstream notice gives no separate version | Apache-2.0 / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| Open Iconic | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| react bootstrap | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| fzyjs | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| sprintfjs | bundled with Streamlit 1.66.0; upstream notice gives no separate version | BSD-3-Clause / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |
| decamelize | bundled with Streamlit 1.66.0; upstream notice gives no separate version | MIT / permissive | [upstream](https://github.com/streamlit/streamlit/tree/1.66.0/frontend/app/src/assets) | [upstream NOTICES](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) |

## Repository assets and copied code

The file-level [installed asset/data inventory](THIRD_PARTY_LICENSES/assets-inventory.json) records paths, versions, hashes and license evidence for dependency fonts, images, audio, sample data and model files. Parent distribution licenses apply unless an explicit bundled-component notice states otherwise. No model-weight file is present in the audited runtime.


No third-party drawing, seal, photo, audio, dataset or model weights are tracked in this source repository. Sample drawing/seal fixtures are generated by the repository’s own example/test code. User-supplied documents and stamps are not relicensed by MIT. A scan of project source found no Stack Overflow, blog, “copied from”, “taken from” or third-party copyright headers requiring additional attribution. Third-party notices above are preserved independently.

## Reproduced Apache NOTICE text

### pyarrow/pyarrow-26.0.0.dist-info/licenses/NOTICE.txt

```text
Apache Arrow
Copyright 2016-2026 The Apache Software Foundation

This product includes software developed at
The Apache Software Foundation (http://www.apache.org/).

This product includes software from the SFrame project (BSD, 3-clause).
* Copyright (C) 2015 Dato, Inc.
* Copyright (c) 2009 Carnegie Mellon University.

This product includes software from the Feather project (Apache 2.0)
https://github.com/wesm/feather

This product includes software from the DyND project (BSD 2-clause)
https://github.com/libdynd

This product includes software from the LLVM project
 * distributed under the University of Illinois Open Source

This product includes software from the mman-win32 project
 * Copyright https://code.google.com/p/mman-win32/
 * Licensed under the MIT License;

This product includes software from the LevelDB project
 * Copyright (c) 2011 The LevelDB Authors. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * Moved from Kudu http://github.com/cloudera/kudu

This product includes software from the CMake project
 * Copyright 2001-2009 Kitware, Inc.
 * Copyright 2012-2014 Continuum Analytics, Inc.
 * All rights reserved.

This product includes software from https://github.com/matthew-brett/multibuild (BSD 2-clause)
 * Copyright (c) 2013-2016, Matt Terry and Matthew Brett; all rights reserved.

This product includes software from the Ibis project (Apache 2.0)
 * Copyright (c) 2015 Cloudera, Inc.
 * https://github.com/cloudera/ibis

This product includes software from Dremio (Apache 2.0)
  * Copyright (C) 2017-2018 Dremio Corporation
  * https://github.com/dremio/dremio-oss

This product includes software from Google Guava (Apache 2.0)
  * Copyright (C) 2007 The Guava Authors
  * https://github.com/google/guava

This product include software from CMake (BSD 3-Clause)
  * CMake - Cross Platform Makefile Generator
  * Copyright 2000-2019 Kitware, Inc. and Contributors

The web site includes files generated by Jekyll.

--------------------------------------------------------------------------------

This product includes code from Apache Kudu, which includes the following in
its NOTICE file:

  Apache Kudu
  Copyright 2016 The Apache Software Foundation

  This product includes software developed at
  The Apache Software Foundation (http://www.apache.org/).

  Portions of this software were developed at
  Cloudera, Inc (http://www.cloudera.com/).

--------------------------------------------------------------------------------

This product includes code from Apache ORC, which includes the following in
its NOTICE file:

  Apache ORC
  Copyright 2013-2019 The Apache Software Foundation

  This product includes software developed by The Apache Software
  Foundation (http://www.apache.org/).

  This product includes software developed by Hewlett-Packard:
  (c) Copyright [2014-2015] Hewlett-Packard Development Company, L.P
```

### requests/requests-2.34.2.dist-info/licenses/NOTICE

```text
Requests
Copyright 2019 Kenneth Reitz
```

Streamlit’s full release-specific third-party NOTICES is reproduced as a separate [preserved file](THIRD_PARTY_LICENSES/streamlit/upstream/NOTICES) (approximately 0.8–0.9 MB), with its per-component inventory above. Retain that file with distributions.
