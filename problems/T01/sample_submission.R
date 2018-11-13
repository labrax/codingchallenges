file <- readLines("stdin", n=1)

df <- read.csv(file, stringsAsFactors=FALSE)
m <- mean(df$value)

cat(file, "\n")
cat(m, "\n")
