file <- readLines("stdin", n=1)

df <- read.csv("sample_df.csv", stringsAsFactors=FALSE)
m <- mean(df$value)

cat(file, "\n")
cat(m, "\n")
