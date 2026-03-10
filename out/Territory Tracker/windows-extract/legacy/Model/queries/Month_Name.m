let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("RZDLCsIwEEV/Zci6i6bvLgVxIagLl6GLtgQValtiI/j35k5M3N17zkwIo5SQIhHHfra9+biUSgqlS5TIHDrowQSbUWzQuWOn3ox3uJx8hCgc2K3mMUEU5CNEyRv8VkkIgBW+YGcNWhEn4JrxxMM1cQJu8La92dcG0dAvQ7WOXPW66eegDWxL/4oBmTp6GbfFe5lSKGxxi/PyDutSUmzscY69HqPPKLau+wI=", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Column1 = _t, Column2 = _t, Column3 = _t]),
    #"Renamed Columns" = Table.RenameColumns(Source,{{"Column3", "Visual Name"}, {"Column2", "Month Name"}, {"Column1", "Month Number"}})
in
    #"Renamed Columns"