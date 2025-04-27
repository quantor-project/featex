#!/usr/bin/env perl
# -*-cperl-*-
## This companion script to featex.perl annotates extracted features in the corpus (as s-attributes). 
## Only token-based features are annotated (/feature[]), those extracted with /feature_count[] are ignored.
$| = 1;

use strict;
use warnings;

use Getopt::Long;
use CWB;
use CWB::CL::Strict;
use CWB::Encoder;

my $Registry = undef;     # -r <dir> (optional)
my $Force = 0;            # -f to overwrite existing s-attributes
my $Prefix = "f_";        # -p <str> (optional prefix for s-attributes)
my $TextAtt = "text_id";  # -t <att> (optional)

my $ok = GetOptions(
  "registry|r=s" => \$Registry,
  "prefix|p=s" => \$Prefix,
  "text-id|text|t=s" => \$TextAtt,
  "force|f" => \$Force,
);

die <<'USAGE' unless $ok && @ARGV == 1;
Usage:  cqp -c -D CORPUS -f script.txt | perl featex-annotate.perl [-t <dir>] [-p <str>] [-r <dir>] [-f] CORPUS
Options:
  -t <att>, --text=<att>      s-attribute containing text IDs (default: "text_id")
  -p <str>, --prefix=<str>    prefix for annotated s-attributes (default: "f_")
  -r <dir>, --registry=<dir>  registry directory (system default otherwise)
  -f, --force                 overwrite existing s-attributes
Arguments:
  CORPUS = CWB handle of corpus (must match corpus used by CQP script)
USAGE

my $Handle = shift @ARGV;

my $RF = new CWB::RegistryFile(defined $Registry ? $Registry."/".lc($Handle) : $Handle);
die "Error: can't find corpus $Handle\n" unless defined $RF;
my $DataDir = $RF->home; # directory for index files
my $modified = 0;

$CWB::CL::Registry = $Registry if defined $Registry;
my $Corpus = new CWB::CL::Corpus $Handle;
my $Word = $Corpus->attribute("word", "p");
my $Text = $Corpus->attribute($TextAtt, "s");
die "Error: s-attribute $Handle.$TextAtt must have annotations\n" unless $Text->struc_values;

my $n_tokens = $Word->max_cpos;
my %TextInfo = ();
foreach my $t (0.. $Text->max_struc - 1) {
  $TextInfo{$Text->struc2str($t)} = [$Text->struc2cpos($t)];
}
printf "Annotationg corpus %s (%d texts, %.1fM tokens)\n", $Handle, scalar %TextInfo, $n_tokens / 1e6;

## start reading output of CQP script
chomp($_ = <STDIN>);
die "Error: you must run CQP in child mode (-c).\n(expected CQP version number, but got: $_)\n"
  unless /^CQP version (3\.(\d+)\.(\d+))$/;
my $version_string = $1;
my $version = 3 + $2 / 1e3 + $3 / 1e6; # e.g. 3.004013 = 3.4.13
our $EOL = "-::-EOL-::-"; # CQP end-of-output marker

## first feature must be text regions + IDs (as "n_token")
chomp($_ = <STDIN>);
die "Error: first feature must be token counts 'n_token'.\n(got: $_)\n"
  unless $_ eq "=====TOKENS n_token";

my $n_annotated = 0;
my $n_texts = 0;
while (<STDIN>) {
  chomp;
  last if $_ eq $EOL;
  my @fields = split /\t/;
  die "Format error: expected 3 TAB-delimited fields, but got: $_\n" unless @fields == 3;
  my ($start, $end, $id) = @fields;
  die "Error: text ID '$id' not found in corpus\n" unless exists $TextInfo{$id};
  my ($ref_start, $ref_end) = @{$TextInfo{$id}};
  die "Error: text ID '$id' should be [$ref_start, $ref_end] but actually is [$start, $end].\n" unless $start == $ref_start && $end == $ref_end;
  $TextInfo{$id} = [-1, -1]; # marker to catch duplicates (which shouldn't happen)
  $n_annotated += $end - $start + 1;
  $n_texts++;
}
die "Error: missing end-of-output marker\n" unless $_ eq $EOL;
printf "Annotations cover %d texts, %.1fM tokens\n", $n_texts, $n_annotated / 1e6;

## now annotate all token-level features
my %F = (); 
while (<STDIN>) {
  chomp;
  die "Error: expected feature declaration, but got: $_\n"
    unless /^=====(TOKENS|COUNTS)\s+(\S+)$/;
  my $is_count = ($1 eq "COUNTS");
  my $feature = $2;
  
  ## skip COUNT features
  if ($is_count) {
    printf " - skipping COUNT feature $feature\n";
    while (<STDIN>) {
      chomp;
      last if $_ eq $EOL;
    }
    die "Error: missing end-of-output marker\n" unless $_ eq $EOL;
    next;
  }
  
  ## check for duplicate / existing features and add to registry entry
  die "Error: duplicate feature name '$feature'.\n" if $F{$feature};
  my $SAtt = $Prefix.$feature;
  printf " - annotate feature %s as <%s> ... ", $feature, $SAtt;
  
  my $existing = $RF->attribute($SAtt);
  if (defined $existing) {
    die "Error: attribute $Handle.$SAtt exists, won't overwrite without --force\n" unless $Force;
    die "Error: can't overwrite $existing-attribute $Handle.$SAtt with s-attribute\n" unless $existing eq "s";
  }
  else {
    $RF->add_attribute($SAtt, "s");
    $modified = 1;
  }

  ## collect feature spans in temporary file
  my $TF = new CWB::TempFile;
  $F{$feature} = 0;
  while (<STDIN>) {
    chomp;
    last if $_ eq $EOL;
    my @fields = split /\t/;
    die "Format error: expected 3 TAB-delimited fields, but got: $_\n" unless @fields == 3;
    my ($start, $end, $id) = @fields;
    die "Error: text ID '$id' not found in corpus\n" unless exists $TextInfo{$id};
    die "Error: invalid token span [$start, $end]\n" unless $start <= $end && $end < $n_tokens;
    $TF->write("$start\t$end\n");
    $F{$feature}++;
  }
  die "Error: missing end-of-output marker\n" unless $_ eq $EOL; 
  $TF->finish;
  
  ## encode new s-attribute
  print "encoding ... ";
  CWB::Shell::Cmd(["cp", $TF->name, "/tmp/featex_$SAtt.txt"]);
  CWB::Shell::Cmd([$CWB::SEncode, "-d", $DataDir, "-f", $TF->name, "-M", "-S", $SAtt]);
  $TF->close;

  printf "%d items\n", $F{$feature};
}

if ($modified) {
  printf "Saving modified registry file %s\n", $RF->filename;
  $RF->write;
}


__END__

## save feature matrix to .tsv file
open(FH, ">", $Outfile) or die "Can't write output file '$Outfile': $!";
print "Saving feature matrix ... ";
print FH join("\t", "id", @Feature), "\n";
foreach my $id (@TextID) {
  print FH $id;
  foreach my $feature (@Feature) {
    print FH "\t", ($F{$feature}{$id} || 0);
  }
  print FH "\n";
}
close(FH);
printf "%s (%.1f MB)\n", $Outfile, (-s $Outfile) / 1e6;
