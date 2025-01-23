

FROM python:3.13-slim
LABEL authors="ehyde74"

RUN pip install mqroute==0.3.2

# Copy your application files (if needed)
COPY pong.py /app/

WORKDIR /app

# Set the ENTRYPOINT or CMD as needed
ENTRYPOINT ["python", "pong.py"]