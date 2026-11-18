FROM alpine:3.20
RUN apk add --no-cache python3 wireguard-tools iptables iptables-legacy iproute2 libqrencode-tools openssl
COPY app.py /app/app.py
ENTRYPOINT ["python3", "-u", "/app/app.py"]
