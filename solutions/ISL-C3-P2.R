file <- readLines("stdin", n=1)
df <- read.csv(file)

y <- df$y
x <- df$x
x2 <- x*x
x3 <- x*x*x
x4 <- x*x*x*x

m <- lm(formula = y ~ x + x2 + x3 + x4, data = df)

rsquared <- 1 - sum((m$fitted.values - df$y)^2) / sum((m$fitted.values - mean(df$y))^2)

e <- summary(m)$coefficients[,4] < 0.001
amt <- sum(e[2:length(e)])


cat(rsquared, "\n")
cat(amt, "\n")
