This is designed to take two parallel corpora of OCR text and original text as input. It will word 
align the OCR errors with their correct couterparts in the original text. We were using the an
OCRed 1911 Britannica and a hand corrected version provided by project Gutenberg. The alignments 
provide training data for the HMM which operates at the word and substring level simultaneously.
The HMM word level source model is provided by Microsofts Ngram server and the character level source 
model is generated from a recent Wikipedia dump. Using Wikipedia is extremely helpful because the 1911 
Britannica contains many different languages and some of these non-english words are OCR errors so the 
German and French that appears in the Wikipedia dump gives the model the ability to handle some of these
OCR errors.

The HMM is modified from NLTK source. Right now I am getting 90% accuracy at correcting OCR errors but there are still improvements to be made. The OCR word level error alignment algorithm generated roughly 150,000 alignments that I am happy
to open source if anyone needs.

OCR error word alignments:

[ 25 characters of left context <(trueWord,OCRerror)> 25 characters of right context ]
where the top line is OCR context and bottom line is true context.
[REG] is a meta-info tag


efore strangers, as they <(believe:beh'eve)>	 that to reveal the m [REG]

efore strangers, as they <(believe:beh'eve)>	 that to reveal the m [REG]



j. spon's histoire de la <(republique:rtpublique)>	 de geneve. a collect [REG]

j. spon's histoire de la <(republique:rtpublique)>	 de geneve. a collect [REG]



ccordance with a clearly <(defined:denned)>	 system, and admirabl [REG]

ccordance with a clearly <(defined:denned)>	 system, and admirabl [REG]



had sent. he also threw <(himself:limself)>	 at his guest's feet, [REG]

had sent. he also threw <(himself:limself)>	 at his guest's feet, [REG]



twards. h is the garden, <(cultivated:cujtivated)>	 by the occupant of t [REG]

twards. h is the garden, <(cultivated:cujtivated)>	 by the occupant of t [REG]
