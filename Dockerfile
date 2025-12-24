# Base image
FROM python:3.9-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt thư viện
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . /app/

# Mở port 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]