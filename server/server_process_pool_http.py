from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

httpserver = HttpServer()

def ProcessTheClient(connection_info):
    """Process client in separate process - receives connection data"""
    connection, address = connection_info
    
    try:
        local_httpserver = HttpServer()
        
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
                        # Determine request type for logging
                        request_type = get_request_type(rcv)
                        print(f"Processing {request_type} from client {address}")
                        hasil = local_httpserver.proses(rcv)
                        # Send response
                        connection.sendall(hasil)
                        print(f"Finished {request_type} from client {address}")
                        break
                    elif rcv.endswith('\r\n') and 'GET' in rcv and 'HTTP' in rcv:
                        # Simple GET request
                        request_type = get_request_type(rcv)
                        print(f"Processing {request_type} from client {address}")
                        hasil = local_httpserver.proses(rcv)
                        connection.sendall(hasil)
                        print(f"Finished {request_type} from client {address}")
                        break
                else:
                    break
            except OSError as e:
                print(f"Socket error: {e}")
                break
        
        connection.close()
        return f"Processed client {address}"
        
    except Exception as e:
        print(f"Error in ProcessTheClient: {e}")
        if connection:
            connection.close()
        return f"Error processing {address}: {str(e)}"

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

def Server():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8889))
    my_socket.listen(10)
    
    print("Process Pool HTTP Server running on port 8889")
    
    active_futures = []
    
    with ProcessPoolExecutor(max_workers=20) as executor:
        try:
            while True:
                connection, client_address = my_socket.accept()
                print(f"Connection from {client_address}")
                
                completed = [f for f in active_futures if f.done()]
                for f in completed:
                    try:
                        result = f.result()
                        print(f"Task result: {result}")
                    except Exception as e:
                        print(f"Task error: {e}")
                    active_futures.remove(f)
                
                future = executor.submit(ProcessTheClient, (connection, client_address))
                active_futures.append(future)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            my_socket.close()

def main():
    if __name__ == "__main__":
        if sys.platform != 'win32':
            multiprocessing.set_start_method('fork', force=True)
        else:
            multiprocessing.set_start_method('spawn', force=True)
    
    Server()

if __name__ == "__main__":
    main()
