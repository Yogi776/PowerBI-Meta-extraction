let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("ZZZLksIwDAXvkjWLSPJHPgvF/a8xEOPJM72Bqq4nRV1gR8/nYcfj8NPG58uP1+N5uJDzIiHELlJQVUEa+nRkEmSgyk5BMZFM/f64EMeeIT9/1SZRNc0UkIqqhkwHSSEmakq+alpmMvWuthVOYvdIDhJCQtUMagY1g5rdT09kBjJLTRGnNmdqEoeaQ82h5nefCtKEbGrSOdF5oM9Sc6o51RRNEnedC9nUAmqSqUL0rCnpqEp0HsgsNWlkxpSMvf6jkxSctXLLBkhBVQVpQvQa0UyCDFQttYJr5EI/Z00LJ6lQq/jVKtQq1CTTQDqqEpkBstQq1T7IclPTwkka/pANau0eqYBUVDVkOkji6QNkqUmZydQ/v1qDWsc10qHWcdY61DrUOtT6/fREZiCz1BRxanOmJkmoJc5aQk2qqpDtrCXUpCrReSCz1KSRcWqTsfdrBNuIYxvRTBGyXf7YRjTTQVLIpqZ7xomQGWY0Z+FFAttIYBsJedEXVFWQhj4dmQQZqPqqTbSpBbeRrXASgxq2kTCoYRvRTAPpqEpkBshSM6p9vvYbMrCNhLzqXcimhm0kHGpS1ZDpeFYiM5BZatxGgtvIlppE3usOEkI2NdlhKkgTsqlhGwlsI9pnqQXVuI38o9cf", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [#"Month Number" = _t, Year = _t, #"Work Days" = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"Month Number", Int64.Type}, {"Year", Int64.Type}, {"Work Days", Int64.Type}}),
    #"Replaced Value" = Table.ReplaceValue(#"Changed Type",1,1,Replacer.ReplaceValue,{"Month Number"}),
    #"Changed Type1" = Table.TransformColumnTypes(#"Replaced Value",{{"Month Number", type text}}),
    #"Replaced Value1" = Table.ReplaceValue(#"Changed Type1","1","01",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value2" = Table.ReplaceValue(#"Replaced Value1","2","02",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value3" = Table.ReplaceValue(#"Replaced Value2","3","03",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value4" = Table.ReplaceValue(#"Replaced Value3","4","04",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value5" = Table.ReplaceValue(#"Replaced Value4","5","05",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value6" = Table.ReplaceValue(#"Replaced Value5","6","06",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value7" = Table.ReplaceValue(#"Replaced Value6","7","07",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value8" = Table.ReplaceValue(#"Replaced Value7","8","08",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value9" = Table.ReplaceValue(#"Replaced Value8","9","09",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value10" = Table.ReplaceValue(#"Replaced Value9","010","10",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value11" = Table.ReplaceValue(#"Replaced Value10","101","11",Replacer.ReplaceText,{"Month Number"}),
    #"Replaced Value12" = Table.ReplaceValue(#"Replaced Value11","102","12",Replacer.ReplaceText,{"Month Number"})
in
    #"Replaced Value12"