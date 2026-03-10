let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("bY5RC4IwFIX/ytizIZr6XsNoYUo26EF8WHVJYWyw3ejvt2UJQo/n+w7n3q6jvKQR5RrBakDaRx0VhSeiIBdwSJiR7ovzgHNyNk8cCAONVqrJZMFk5DjeX/BrrwNbk9pYHGDeSANNQ3O1QSU1jrdJJEEk0/hc52L+TeJo9PceqzxmRim4Beom2FRVyQRv6vMfezh52Php+4ltuYhiu4j7RfKhhatEcDHXDqVS8c7C+Bj8j/0b", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [#"SQL Name" = _t, #"Visual Name" = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"SQL Name", type text}, {"Visual Name", type text}})
in
    #"Changed Type"