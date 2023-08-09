
# Searching for DKIST Datasets

REFERENCE
In DKIST data parlance, a "dataset" is the smallest unit of data that is searchable from the data centre, and represents a single observation from a single instrument at a single pass band.

---

EXPLANATION
For each of these "datasets" the DKIST Data Center keeps a "dataset inventory record" which is a limited set of metadata about the dataset on which you can search, either through the portal or the `dkist` Python package.

---

HOW TO GUIDE

Because `Fido` can search other clients as well as the DKIST you can make a more complex query which will search for VISP data and context images from AIA at the same time:

```{code-cell} python
time = a.Time("2022-06-02 17:00:00", "2022-06-02 18:00:00")
aia = a.Instrument.aia & a.Wavelength(17.1 * u.nm) & a.Sample(30 * u.min)
visp = a.Instrument.visp & a.dkist.Embargoed(False)

Fido.search(time, aia | visp)
```

Here we have used a couple of different attrs `a.Sample` limits the results to one per time window given, and `a.Wavelength` searches for specific wavelengths of data.

---

EXPLANATION
Also, we passed our attrs as positional arguments to `Fido.search` this is a little bit of sugar to prevent having to specify a lot of brackets, all arguments have the and (`&`) operator applied to them.

---

EXPLANATION
A Fido search returns a {obj}`sunpy.net.fido_factory.UnifiedResponse` object, which contains all the search results from all the different clients and requests made to the servers.
```{code-cell} python
res = Fido.search((a.Instrument.vbi | a.Instrument.visp) & a.dkist.Embargoed(False))
type(res)
```
The `UnifiedResponse` object provides a couple of different ways to select the results you are interested in.
It's possible to select just the results returned by a specific client by name, in this case all the results are from the DKIST client so this changes nothing.
```{code-cell} python
res["dkist"]
```

This object is similar to a list of tables, where each response can also be selected by the first index:

Now we have selected a single set of results from the `UnifiedResponse` object, we can see that we have a `DKISTQueryResponseTable` object:
```{code-cell} python
type(vbi)
```
This is a subclass of `astropy.table.QTable`, which means we can do operations such as sorting and filtering with this table.

---

EXPLANATION
With the nature of DKIST data being a large number of files, FITS + ASDF for a whole dataset, we probably want to keep each dataset in its own folder.
`Fido` makes this easy by allowing you to provide a path template rather than a specific path.

---

HOW-TO
To see the list of parameters we can use in these path templates we can run:
```{code-cell} python
vbi.path_format_keys()
```
