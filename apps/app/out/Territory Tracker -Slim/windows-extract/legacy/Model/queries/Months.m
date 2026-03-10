let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i45WMjBU0lHySswrTSyqBLICDZVidYCiRkC2W2pSEZqwMZDtm1iUnIEkZgJkOxYUZeaAxIwgYqZgdZVIImYga0rzUpGEzMFCOWBVxhAhC5BZpemlxSVIgpZAdnBqQUlqblJqEULc0ADI9k8uyYeKmkBEQf7xyy+DK4YKgzzkkpqMLBwLAA==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [#"Month #" = _t, Month = _t, Quarter = _t])
in
    Source