# ========== STAGE 1: Builder ==========
FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY main.go ./

RUN CGO_ENABLED=0 GOOS=linux go build \
    -a \
    -installsuffix cgo \
    -ldflags="-s -w" \
    -o devops-service .

# ========== STAGE 2: Runtime ==========
FROM alpine:3.19 AS runtime

RUN apk add --no-cache ca-certificates tzdata

RUN addgroup -S appgroup && adduser -S mariaappgo -G appgroup

WORKDIR /app

COPY --from=builder /app/devops-service /app/

RUN chown -R mariaappgo:appgroup /app

USER mariaappgo

EXPOSE 5001

ENV PORT=5001

CMD ["./devops-service"]