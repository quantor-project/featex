IMPORT macros/mwus.m


MACRO feature($0=NQR)
  cat "=====TOKENS $0\n";
  tabulate $0 match, matchend, match /_sattr[];
  .EOL.;
;

MACRO feature_count($0=NQR)
  cat "=====COUNTS $0\n";
  group $0 match /_sattr[];
  .EOL.;
;

MACRO init($0=name)
  define macro _sattr(0) "$0";
  Corpus = [] expand to $0;
  /feature[Corpus];
  Corpus; # activate
;

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
