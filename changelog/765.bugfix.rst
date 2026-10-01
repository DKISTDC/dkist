Fix 3D `~dkist.wcs.models.VaryingCelestialTransform` lookups that ignored the third index.
Return NaN for inverse lookups outside the table.
Allow scalar pixel coordinates without units alongside an array of lookup indices.
