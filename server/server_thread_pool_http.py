from socket import *
import socket
import time
import sys
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from http import HttpServer

httpserver = HttpServer()

def get_request_type(request_data):
    """Determine the type of request for logging"""
    try:
        lines = request_data.split('\n')
        if lines:
            first_line = lines[0].strip()
            
            # Check for file listing
            if 'GET' in first_line and '/files' in first_line:
                return "list file"
            
            # Check for file upload
            elif 'POST' in first_line and ('upload' in first_line or 'files' in first_line):
                return "upload file"
            
            # Check for file deletion
            elif 'DELETE' in first_line:
                return "delete file"
            
            # Default cases
            elif 'GET' in first_line:
                return "GET request"
            elif 'POST' in first_line:
                return "POST request"
            else:
                return "unknown request"
    except:
        return "unknown request"

def ProcessTheClient(connection, address):
    """Process client request in a separate thread"""
    try:
        print(f"Thread {threading.current_thread().ident} handling client {address}")
        
        rcv = ""
        while True:
            try:
                data = connection.recv(4096)
                if data:
                    # Convert bytes to string for processing
                    d = data.decode('utf-8', errors='ignore')
                    rcv = rcv + d
                    
                    # Check for complete HTTP request
                    if '\r\n\r\n' in rcv:
                        # Complete HTTP request received, process it
                        request_type = get_request_type(rcv)
                        print(f"Processing {request_type} from client {address}")
                        hasil = httpserver.proses(rcv)
                        connection.sendall(hasil)
                        print(f"Finished {request_type} from client {address}")
                        break
                    elif rcv.endswith('\r\n') and ('GET' in rcv or 'POST' in rcv or 'DELETE' in rcv) and 'HTTP' in rcv:
                        # Simple request (like GET /files)
                        request_type = get_request_type(rcv)
                        print(f"Processing {request_type} from client {address}")
                        hasil = httpserver.proses(rcv)
                        connection.sendall(hasil)
                        print(f"Finished {request_type} from client {address}")
                        break
                else:
                    break
            except OSError as e:
                print(f"Socket error with {address}: {e}")
                break
        
        connection.close()
        print(f"Thread {threading.current_thread().ident} completed processing {address}")
        return f"Successfully processed {address}"
        
    except Exception as e:
        print(f"Error in ProcessTheClient for {address}: {e}")
        if connection:
            connection.close()
        return f"Error processing {address}: {str(e)}"

def Server():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8885))
    my_socket.listen(10)
    
    print("Thread Pool HTTP Server running on port 8885")
    print(f"Main thread ID: {threading.current_thread().ident}")
    
    active_futures = []
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        try:
            while True:
                connection, client_address = my_socket.accept()
                print(f"New connection from {client_address}")
                
                completed_futures = [f for f in active_futures if f.done()]
                for future in completed_futures:
                    try:
                        result = future.result()
                        print(f"Task completed: {result}")
                    except Exception as e:
                        print(f"Task failed: {e}")
                    active_futures.remove(future)
                
                future = executor.submit(ProcessTheClient, connection, client_address)
                active_futures.append(future)
                
        except KeyboardInterrupt:
            print("\nReceived interrupt signal. Shutting down server...")
            
            if active_futures:
                print(f"Waiting for {len(active_futures)} active threads to complete...")
                for future in as_completed(active_futures, timeout=10):
                    try:
                        result = future.result()
                        print(f"Thread completed: {result}")
                    except Exception as e:
                        print(f"Thread error: {e}")
                        
        except Exception as e:
            print(f"Server error: {e}")
            
        finally:
            print("Closing server socket...")
            my_socket.close()

def main():
    Server()

if __name__ == "__main__":
    main()