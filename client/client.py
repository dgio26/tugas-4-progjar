import socket
import os
import sys
from urllib.parse import quote

class HttpClient:
    def __init__(self, host='172.16.16.101', port=8885):
        self.host = host
        self.port = port
    
    def send_request(self, request):
        """Send HTTP request and return response"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            
            client_socket.send(request.encode())
            
            response = b""
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data
                if b'\r\n\r\n' in response:
                    break
            
            client_socket.close()
            return response.decode('utf-8', errors='ignore')
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def list_files(self):
        """Get directory listing from server"""
        request = "GET /files HTTP/1.0\r\n\r\n"
        response = self.send_request(request)
        
        if "200 OK" in response:
            html_start = response.find('<html>')
            if html_start != -1:
                html_content = response[html_start:]
                print("\n=== Directory Listing ===")
                if '<tr>' in html_content:
                    rows = html_content.split('<tr>')
                    for row in rows[2:]:  # Skip header rows
                        if '<td>' in row:
                            cells = row.split('<td>')
                            if len(cells) >= 4:
                                filename = cells[1].split('</td>')[0]
                                filesize = cells[2].split('</td>')[0]
                                modified = cells[3].split('</td>')[0]
                                print(f"File: {filename} | Size: {filesize} bytes | Modified: {modified}")
                else:
                    print("No files found in directory")
            else:
                print("Could not parse directory listing")
        else:
            print("Failed to get directory listing")
            print(response)
    
    def upload_file(self, filepath):
        """Upload a file to the server"""
        if not os.path.exists(filepath):
            print(f"Error: File {filepath} not found")
            return
        
        filename = os.path.basename(filepath)
        
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
            
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            
            body_parts = []
            body_parts.append(f"------WebKitFormBoundary7MA4YWxkTrZu0gW")
            body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
            body_parts.append("Content-Type: application/octet-stream")
            body_parts.append("")
            
            header_part = "\r\n".join(body_parts) + "\r\n"
            
            body = header_part.encode() + file_content + f"\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n".encode()
            
            request_lines = [
                "POST /upload HTTP/1.0",
                f"Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
                f"Content-Length: {len(body)}",
                "",
                ""
            ]
            
            request_header = "\r\n".join(request_lines)
            request = request_header.encode() + body
            
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            client_socket.send(request)
            
            response = b""
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data
                if b'\r\n\r\n' in response:
                    break
            
            client_socket.close()
            
            response_str = response.decode('utf-8', errors='ignore')
            if "200 OK" in response_str:
                print(f"Successfully uploaded {filename}")
            else:
                print(f"Failed to upload {filename}")
                print(response_str)
                
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
    
    def delete_file(self, filename):
        """Delete a file from the server"""
        encoded_filename = quote(filename)
        request = f"DELETE /delete/{encoded_filename} HTTP/1.0\r\n\r\n"
        
        response = self.send_request(request)
        
        if "200 OK" in response:
            print(f"Successfully deleted {filename}")
        elif "404 Not Found" in response:
            print(f"File {filename} not found")
        else:
            print(f"Failed to delete {filename}")
            print(response)

def main():
    print("=== HTTP File Client ===")
    print("Make sure your HTTP server is running on 172.16.16.101:8885")
    
    host = "172.16.16.101"
    port = 8885
    
    client = HttpClient(host, port)
    
    while True:
        print("\n=== Menu ===")
        print("1. List file")
        print("2. Upload file")
        print("3. Delete file")
        print("4. Exit")
        
        choice = input("\nPilih opsi (1-4): ").strip()
        
        if choice == '1':
            print("Fetching file list...")
            client.list_files()
            
        elif choice == '2':
            filepath = input("Enter path to file to upload: ").strip()
            if filepath:
                print(f"Uploading {filepath}...")
                client.upload_file(filepath)
            else:
                print("Please provide a file path")
                
        elif choice == '3':
            print("Current files on server:")
            client.list_files()
            
            filename = input("\nEnter filename to delete: ").strip()
            if filename:
                confirm = input(f"Are you sure you want to delete '{filename}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    print(f"Deleting {filename}...")
                    client.delete_file(filename)
                else:
                    print("Delete cancelled")
            else:
                print("Please provide a filename")
                
        elif choice == '4':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()