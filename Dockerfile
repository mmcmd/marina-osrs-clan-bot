# Use the latest stable Python image (can be specific if needed)
FROM python:latest

# Set the working directory within the container
WORKDIR /app

# Copy the current directory (context) and its contents to the container's /app directory
COPY . .

# Install pip packages listed in a requirements.txt file (optional)
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot.py script using the latest stable Python version
CMD ["python", "bot.py"]