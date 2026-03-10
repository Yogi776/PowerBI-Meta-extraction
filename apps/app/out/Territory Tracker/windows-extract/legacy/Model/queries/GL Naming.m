let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("dVPLTsNADPyXnHvwYx/dOwL1VtFj1UNAEUSKUqnZ/j9tYEF43KNnx2N7vD4eu0DE1G26Qz8NS3fa3JHtirwO9XqZG0YCLHFYCix1WAFYwWFFYEWHlYCVPFYEVgQWgxPFcaIEJzNYfQa/4oo8jcv7+TrXJuaYWKJTINoCmk0B5oxaAiMJNCawNFFbTeyATGgNE07DhB+AybFQbV/MjjdqO2NWR8tOdGM53sDXkS0i4DtZhOwmbtsCHUQgS4pFFLan+N2drRc8FCYPw1ymghg7u05kPY6r2vNlGD8+a8N+1N76+svLq9puXmo/TX0dz3N7kEcP6dGDYskcHAxbI7UnxYyHx98HtH/ZtVhNnEyc/8f6l3/6Ag==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [#"GL Code" = _t, #"Visual_GL Name" = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"GL Code", Int64.Type}, {"Visual_GL Name", type text}})
in
    #"Changed Type"