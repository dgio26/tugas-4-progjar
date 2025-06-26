import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import urllib.parse
import json

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
		
	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")
		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()
		response = response_headers.encode() + messagebody
		return response
		
	def parse_multipart_data(self, body, boundary):
		"""Parse multipart form data untuk file upload"""
		parts = body.split(('--' + boundary).encode())
		files = {}
		
		for part in parts:
			if b'Content-Disposition' in part:
				lines = part.split(b'\r\n')
				content_disposition = None
				filename = None
				
				for line in lines:
					if b'Content-Disposition' in line:
						content_disposition = line.decode()
						if 'filename=' in content_disposition:
							filename = content_disposition.split('filename=')[1].strip('"')
						break
				
				if filename:
					data_start = part.find(b'\r\n\r\n')
					if data_start != -1:
						file_data = part[data_start + 4:]
						if file_data.endswith(b'\r\n'):
							file_data = file_data[:-2]
						files[filename] = file_data
		
		return files
		
	def proses(self,data):
		requests = data.split("\r\n")
		#print(requests)
		baris = requests[0]
		#print(baris)
		all_headers = [n for n in requests[1:] if n!='']
		
		body = ""
		if "\r\n\r\n" in data:
			body_start = data.find("\r\n\r\n") + 4
			body = data[body_start:]
		
		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			if (method=='POST'):
				object_address = j[1].strip()
				return self.http_post(object_address, all_headers, body)
			if (method=='DELETE'):
				object_address = j[1].strip()
				return self.http_delete(object_address, all_headers)
			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})
			
	def http_get(self,object_address,headers):
		files = glob('./*')
		#print(files)
		thedir='./'
		if (object_address == '/'):
			return self.response(200,'OK','Ini Adalah web Server percobaan',dict())
		if (object_address == '/video'):
			return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
		if (object_address == '/santai'):
			return self.response(200,'OK','santai saja',dict())
		
		if (object_address == '/files'):
			return self.list_directory_files(thedir)
		
		object_address=object_address[1:]
		if thedir+object_address not in files:
			return self.response(404,'Not Found','',{})
		fp = open(thedir+object_address,'rb') #rb => artinya adalah read dalam bentuk binary
		#harus membaca dalam bentuk byte dan BINARY
		isi = fp.read()
		fp.close()
		
		fext = os.path.splitext(thedir+object_address)[1]
		content_type = self.types.get(fext, 'application/octet-stream')
		
		headers={}
		headers['Content-type']=content_type
		
		return self.response(200,'OK',isi,headers)
		
	def list_directory_files(self, directory):
		"""List semua file dalam direktori"""
		try:
			files = []
			for item in os.listdir(directory):
				if os.path.isfile(os.path.join(directory, item)):
					file_info = {
						'name': item,
						'size': os.path.getsize(os.path.join(directory, item)),
						'modified': datetime.fromtimestamp(os.path.getmtime(os.path.join(directory, item))).strftime('%Y-%m-%d %H:%M:%S')
					}
					files.append(file_info)
			
			html_content = """
			<!DOCTYPE html>
			<html>
			<head>
				<title>Directory Listing</title>
				<style>
					table { border-collapse: collapse; width: 100%; }
					th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
					th { background-color: #f2f2f2; }
				</style>
			</head>
			<body>
				<h1>Directory Files</h1>
				<table>
					<tr>
						<th>File Name</th>
						<th>Size (bytes)</th>
						<th>Last Modified</th>
					</tr>
			"""
			
			for file_info in files:
				html_content += f"""
					<tr>
						<td>{file_info['name']}</td>
						<td>{file_info['size']}</td>
						<td>{file_info['modified']}</td>
					</tr>
				"""
			
			html_content += """
				</table>
				<br>
				<h2>Upload File</h2>
				<form action="/upload" method="post" enctype="multipart/form-data">
					<input type="file" name="file" required>
					<input type="submit" value="Upload">
				</form>
			</body>
			</html>
			"""
			
			headers = {'Content-type': 'text/html'}
			return self.response(200, 'OK', html_content, headers)
			
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'Error listing directory: {str(e)}', {})
	
	def http_post(self,object_address,headers, body):
		# Handle file upload
		if object_address == '/upload':
			return self.handle_file_upload(headers, body)
		
		headers ={}
		isi = "kosong"
		return self.response(200,'OK',isi,headers)
		
	def handle_file_upload(self, headers, body):
		"""Handle file upload dari form multipart"""
		try:
			content_type_header = None
			for header in headers:
				if header.lower().startswith('content-type:'):
					content_type_header = header
					break
			
			if not content_type_header or 'multipart/form-data' not in content_type_header:
				return self.response(400, 'Bad Request', 'Invalid content type for file upload', {})
			
			boundary = None
			if 'boundary=' in content_type_header:
				boundary = content_type_header.split('boundary=')[1].strip()
			
			if not boundary:
				return self.response(400, 'Bad Request', 'Missing boundary in multipart data', {})
			
			files = self.parse_multipart_data(body.encode() if isinstance(body, str) else body, boundary)
			
			if not files:
				return self.response(400, 'Bad Request', 'No file found in upload', {})
			
			uploaded_files = []
			for filename, file_data in files.items():
				try:
					with open('./' + filename, 'wb') as f:
						f.write(file_data)
					uploaded_files.append(filename)
				except Exception as e:
					return self.response(500, 'Internal Server Error', f'Error saving file {filename}: {str(e)}', {})
			
			response_html = f"""
			<!DOCTYPE html>
			<html>
			<body>
				<h1>Upload Successful</h1>
				<p>Files uploaded: {', '.join(uploaded_files)}</p>
				<a href="/files">Back to file list</a>
			</body>
			</html>
			"""
			
			headers = {'Content-type': 'text/html'}
			return self.response(200, 'OK', response_html, headers)
			
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'Upload error: {str(e)}', {})
	
	def http_delete(self, object_address, headers):
		"""Handle file deletion"""
		try:
			if not object_address.startswith('/delete/'):
				return self.response(400, 'Bad Request', 'Invalid delete URL format. Use /delete/filename', {})
			
			filename = object_address[8:]  # Remove '/delete/' prefix
			if not filename:
				return self.response(400, 'Bad Request', 'No filename specified', {})
			
			filename = urllib.parse.unquote(filename)
			
			filepath = './' + filename
			
			if not os.path.exists(filepath):
				return self.response(404, 'Not Found', f'File {filename} not found', {})
			
			if not os.path.isfile(filepath):
				return self.response(400, 'Bad Request', f'{filename} is not a file', {})
			
			os.remove(filepath)
			
			response_html = f"""
			<!DOCTYPE html>
			<html>
			<body>
				<h1>Delete Successful</h1>
				<p>File '{filename}' has been deleted.</p>
				<a href="/files">Back to file list</a>
			</body>
			</html>
			"""
			
			headers = {'Content-type': 'text/html'}
			return self.response(200, 'OK', response_html, headers)
			
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'Delete error: {str(e)}', {})
		
			 	
if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
	print(d)
