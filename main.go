package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
)

type Response struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Log     string `json:"log,omitempty"`
}

func main() {
	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/upload", uploadHandler)
	http.HandleFunc("/files", filesHandler)
	http.HandleFunc("/columns", columnsHandler)
	http.HandleFunc("/partition", partitionHandler)

	fs := http.FileServer(http.Dir("./static"))

	http.Handle("/static/", http.StripPrefix("/static/", fs))

	fmt.Println("Server is listening on port 8080.")
	http.ListenAndServe(":8080", nil)
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "static/index.html")
}

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		json.NewEncoder(w).Encode(Response{Success: false, Message: "Unable to upload file."})
		return
	}

	defer file.Close()

	out, err := os.Create("uploads/" + header.Filename)
	if err != nil {
		json.NewEncoder(w).Encode(Response{Success: false, Message: "Unable to create the file for writing."})
		return
	}
	defer out.Close()

	_, err = io.Copy(out, file)
	if err != nil {
		json.NewEncoder(w).Encode(Response{Success: false, Message: "Unable to save the file."})
		return
	}

	json.NewEncoder(w).Encode(Response{Success: true, Message: "File uploaded successfully: " + header.Filename})
}

func columnsHandler(w http.ResponseWriter, r *http.Request) {
	file := r.URL.Query().Get("file")
	if file == "" {
		http.Error(w, "File name is required.", http.StatusBadRequest)
		return
	}

	f, err := os.Open(filepath.Join("uploads", file))
	if err != nil {
		http.Error(w, "Unable to open the file.", http.StatusInternalServerError)
		return
	}
	defer f.Close()

	reader := csv.NewReader(f)
	columns, err := reader.Read()
	if err != nil {
		http.Error(w, "Unable to read file columns.", http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(map[string][]string{"columns": columns})
}

func partitionHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		File    string   `json:"file"`
		Columns []string `json:"columns"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body.", http.StatusBadRequest)
		return
	}

	filename := filepath.Join("uploads", req.File)
	args := append([]string{"main.py", filename}, req.Columns...)
	cmd := exec.Command("python3", args...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		json.NewEncoder(w).Encode(Response{Success: false, Message: fmt.Sprintf("Error executing script: %v", err), Log: string(output)})
		return
	}

	json.NewEncoder(w).Encode(Response{Success: true, Message: "Partitioning completed.", Log: string(output)})
}

func filesHandler(w http.ResponseWriter, r *http.Request) {
	dirEntries, err := os.ReadDir("uploads")
	if err != nil {
		http.Error(w, "Unable to read uploaded files directory.", http.StatusInternalServerError)
		return
	}

	var filenames []string
	for _, entry := range dirEntries {
		if !entry.IsDir() {
			filenames = append(filenames, entry.Name())
		}
	}

	json.NewEncoder(w).Encode(map[string][]string{"files": filenames})
}
