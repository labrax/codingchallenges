file <- readLines("stdin", n=1)
df <- read.csv(file)

m <- lm(formula = y ~ x, data = df)

rsquared <- 1 -  sum((m$fitted.values - df$y)^2) / sum((m$fitted.values - mean(df$y))^2)

cat(m$coefficients[2], "\n")
cat(rsquared, "\n")