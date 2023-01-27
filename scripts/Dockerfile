FROM python:3.9-alpine

COPY ./ ./

RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple\
    && pip3 install flask requests -i https://pypi.tuna.tsinghua.edu.cn/simple\
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo Asia/Shanghai > /etc/timezone
