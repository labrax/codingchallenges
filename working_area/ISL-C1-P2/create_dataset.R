
FILE = "mvar.csv"
AMT_POINTS = 100
noise = runif(AMT_POINTS)*500 - 250
noise = sort(runif(AMT_POINTS)) * noise
noise1 = sin(c(1:AMT_POINTS))*noise

noise = runif(AMT_POINTS)*500 - 250
noise = sort(runif(AMT_POINTS), decreasing=TRUE) * noise
noise2 = sin(c(1:AMT_POINTS))*noise

noise = runif(AMT_POINTS)*500 - 250
noise = sort(runif(AMT_POINTS)) * noise
noise3 = sin(c(1:AMT_POINTS))*noise

x_ = sort(runif(AMT_POINTS) * 1000)

x = x_
x2 = x*x
x3 = x*x*x
x4 = x*x*x*x
x5 = x*x*x*x*x
x6 = x*x*x*x*x*x
x7 = x*x*x*x*x*x*x
y = 20 + 2.2 * (x - noise)+ 15 * (x2 - noise2) + 0.5 * (x3 - noise3) + 0.03 * x4
df <- data.frame(x=x, y=y)
write.csv(df, file = FILE, row.names=F)


#file <- readLines("stdin", n=1)
#df <- read.csv(file)

df <- read.csv(file = FILE)
m <- lm(formula = y ~ x + x2 + x3 + x4 + x5 + x6, data = df)
plot(df)
summary(m)

cat(m$coefficients[2])

summary(m)

e <- summary(m)$coefficients[,4] < 0.001
amt <- sum(e[2:length(e)])
amt
