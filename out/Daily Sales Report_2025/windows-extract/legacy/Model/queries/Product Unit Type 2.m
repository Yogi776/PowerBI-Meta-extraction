let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("jZTdasMwDIVfJeS6F2WM3Xte0hii2ciOU+hKGa1ZAmMZSfb+S/fDiCWYbz+s46Mj2YdD7gpZ5Ztcz10YszKEKT9uDnkt7im0ssGFtt3wGrLdMFx+qNDXs+9zP7xN2dPHdntzl4nzOUzTMPZ/tWY5ZZ7H+RvI2ogVKAjYryv2rUBqqkR3LSvH0L908xc6LSxCUImaWgfFUVWnNKRiuyftmCABUsQAIjEwBFRcA0axVHMUWklpxWUKmk1LVw+UskMxO7VADHM/hssvuY2QNeqR6pmk9E2cPibljHHOCJrpCQvraFMIjlv/JL829mttA0zEthUJ2+KQGU9jLEtT7DXxunmhaADSFxjN0HvDXCr1+uX6pIw8+QCWOVDx4n+x4yc=", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [ProductClass = _t, #"Product Unit Type" = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"ProductClass", type text}, {"Product Unit Type", type text}})
in
    #"Changed Type"