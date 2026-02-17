let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("fdK9akMxDAXgd/EsK/q1rTFkSWmGUrJd8v6vkUvpoEHO4EFgPo7EOY7GF74IiTVonccEDkKiczJSp07c6W/8/8Pn+3n0q/7eH7f+/fVsLziaZMQWsAj6HpES0YRIOIjppyRaIpaTiIH6RNItYiXiGZkDVgRKbBEvkZEQPdfRqei8RUaJzJyECXidh51bZJbIyodlBnFBtS2ySiQS4uQQSzH2SaJEmHIUWTDDMNa+bVQzubSiCroYTfZM3VrOtR00IGKif2CK3r7e", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [JnlDate = _t, EntryValue = _t, GlCode = _t, GlYear = _t, GlPeriod = _t, SubModStock = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"JnlDate", type datetime}, {"EntryValue", type number}, {"GlYear", type number}, {"GlPeriod", type number}})
in
    #"Changed Type"