#FROM python:3.10-alpine
#RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
#RUN apk add --no-cache gcc libc-dev libpq-dev
FROM python:3.10-slim
RUN sed -i "s@http://\(deb\|security\).debian.org@https://mirrors.aliyun.com@g" /etc/apt/sources.list
RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc libc-dev libsasl2-dev libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir psycopg2 -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "django_project.asgi:application"]
