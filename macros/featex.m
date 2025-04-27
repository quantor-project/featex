## tabulate instances of a feature
MACRO feature($0=NQR $1=feature)
  cat $0 0 0 > "| echo '=====TOKENS $1'";
  tabulate $0 match, matchend, match /_text_id[];
  .EOL.;
;

MACRO feature($0=NQR)
  /feature[$0, "$0"]
  cat "=====TOKENS $0\n";
;

## generate per-text frequency counts directly
MACRO feature_count($0=NQR $1=feature)
  cat $0 0 0 > "| echo '=====COUNTS $1'";
  group $0 match /_text_id[];
  .EOL.;
;

MACRO feature_count($0=NQR)
  /feature_count[$0, "$0"]
;

## initialize feature extraction (for full corpus or subcorpus)
MACRO init_corpus($0=text_id)
  define macro _text_id(0) "$0";
  _Texts = <$0> [] expand to $0;
  /feature[_Texts, "n_token"];
  discard _Texts;
;

MACRO init_subcorpus($0=Subcorpus $1=text_id)
  define macro _text_id(0) "$1";
  $0 = $0 expand to $1;
  /feature[$0, "n_token"];
  $0; # activate subcorpus
;

## aggregate two or more named query results
MACRO union($0=Res $1=Q1 $2=Q2)
  $0 = union $1 $2;
;

MACRO union($0=Res $1=Q1 $2=Q2 $3=Q3)
  _Union_$$ = union $1 $2;
  $0 = union _Union_$$ $3;
  discard _Union_$$;
;

MACRO union($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4)
  /union[_Union_$$, $1, $2, $3];
  $0 = union _Union_$$ $4;
  discard _Union_$$;
;

MACRO union($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4 $5=Q5)
  /union[_Union_$$, $1, $2, $3, $4];
  $0 = union _Union_$$ $5;
  discard _Union_$$;
;

MACRO union($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4 $5=Q5 $6=Q6)
  /union[_Union_$$, $1, $2, $3, $4, $5];
  $0 = union _Union_$$ $6;
  discard _Union_$$;
;

MACRO union($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4 $5=Q5 $6=Q6 $7=Q7)
  /union[_Union_$$, $1, $2, $3, $4, $5, $6];
  $0 = union _Union_$$ $7;
  discard _Union_$$;
;

## set difference for two or more NQRs (remove matches of second, third, ... from first NQR)
MACRO diff($0=Res $1=Q1 $2=Q2)
  $0 = diff $1 $2;
;

MACRO diff($0=Res $1=Q1 $2=Q2 $3=Q3)
  _Diff_$$ = diff $1 $2;
  $0 = diff _Diff_$$ $3;
  discard _Diff_$$;
;

MACRO diff($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4)
  /diff[_Diff_$$, $1, $2, $3];
  $0 = diff _Diff_$$ $4;
  discard _Diff_$$;
;

MACRO diff($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4 $5=Q5)
  /diff[_Diff_$$, $1, $2, $3, $4];
  $0 = diff _Diff_$$ $5;
  discard _Diff_$$;
;

MACRO diff($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4 $5=Q5 $6=Q6)
  /diff[_Diff_$$, $1, $2, $3, $4, $5];
  $0 = diff _Diff_$$ $6;
  discard _Diff_$$;
;

MACRO diff($0=Res $1=Q1 $2=Q2 $3=Q3 $4=Q4 $5=Q5 $6=Q6 $7=Q7)
  /diff[_Diff_$$, $1, $2, $3, $4, $5, $6];
  $0 = diff _Diff_$$ $7;
  discard _Diff_$$;
;
