.. _dkist:topic-guides:productid:

Product IDs and Dataset IDs
===========================

A DKIST dataset is built from a single calibration of observe frames as well as calibration frames (such as darks and flats).
Each run of a calibration pipeline results in a different Dataset ID, which uniquely represents that dataset.

A DKIST product is a defined by the set of observe frames, so a Product ID uniquely identifies that set of observe frames.
When the data is recalibrated different calibration frames may be used, but each unique set of observe frames generates a unique Product ID.

Searching by Product ID
-----------------------

We expect that most commonly people will search by Product ID, and use the most recently calibrated version of that product.
All searches by default only return the latest calibration of a Product ID.

Searching by Product ID can be done using `~dkist.net.attrs.Product`:

.. code-block:: python

    >>> from sunpy.net import Fido, attrs as a
    >>> import dkist.net

    >>> Fido.search(a.dkist.Product("L1-YEVFH"))  # doctest: +REMOTE_DATA
    <sunpy.net.fido_factory.UnifiedResponse object at ...>
    Results from 1 Provider:
    <BLANKLINE>
    1 Results from the DKISTClient:
    <BLANKLINE>
    Product ID Dataset ID        Start Time               End Time        Instrument   Wavelength
                                                                                           nm
    ---------- ---------- ----------------------- ----------------------- ---------- --------------
      L1-YEVFH      ...   2022-06-02T17:22:50.176 2022-06-02T17:47:30.856        VBI 486.0 .. 486.0
    <BLANKLINE>
    <BLANKLINE>

Dataset Status
==============

The status of a Dataset indicates if it's the latest calibration for that Product (``ACTIVE``), if it's an older calibration but still available (``DEPRECATED``) or no longer available (``REMOVED``).
It's possible to query a specific dataset ID irrespective of its current status using the `~dkist.net.attrs.Status` attr:

.. code-block:: python

   >>> Fido.search(a.dkist.Dataset("BLKGA"), a.dkist.Status("any"))  # doctest: +REMOTE_DATA
   <sunpy.net.fido_factory.UnifiedResponse object at ...>
   Results from 3 Providers:
   <BLANKLINE>
   1 Results from the DKISTClient:
   <BLANKLINE>
   Product ID Dataset ID        Start Time               End Time        Instrument   Wavelength
                                                                                          nm
   ---------- ---------- ----------------------- ----------------------- ---------- --------------
     L1-YEVFH      ...   2022-06-02T17:22:50.176 2022-06-02T17:47:30.856        VBI 486.0 .. 486.0
   <BLANKLINE>
   0 Results from the DKISTClient:
   <BLANKLINE>
   <No columns>
   <BLANKLINE>
   0 Results from the DKISTClient:
   <BLANKLINE>
   <No columns>
   <BLANKLINE>
   <BLANKLINE>

This query currently returns one result table for each status.
