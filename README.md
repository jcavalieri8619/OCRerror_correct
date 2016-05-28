This is designed to take two parallel corpora of OCR text and original text as input. It will word 
align the OCR errors with their correct couterparts in the original text. We were using the an
OCRed 1911 Britannica and a hand corrected version provided by project Gutenberg. The alignments 
provide training data for the HMM which operates at the word and substring level simultaneously.  
Right now I am getting 90% accuracy at correcting OCR errors but there are still improvements to be made. 
