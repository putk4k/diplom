document.getElementById('uploadForm').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('log').innerText = data.message;
        if (data.success) {
            fetchUploadedFiles();
        }
    })
    .catch(error => console.error('Error:', error));
});

function fetchUploadedFiles() {
    fetch('/files')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('uploadedFiles');
            select.innerHTML = data.files.map(file => `<option value="${file}">${file}</option>`).join('');
            if (data.files.length > 0) {
                fetchColumns(); // Load columns for the first file in the list
            } else {
                document.getElementById('columns').innerHTML = '';
            }
        })
        .catch(error => console.error('Error:', error));
}

function fetchColumns() {
    const file = document.getElementById('uploadedFiles').value;
    fetch(`/columns?file=${file}`)
        .then(response => response.json())
        .then(data => {
            const columnsDiv = document.getElementById('columns');
            columnsDiv.innerHTML = data.columns.map(column => `
                <label>
                    <input type="checkbox" name="columns" value="${column}"> ${column}
                </label>
            `).join('');
        })
        .catch(error => console.error('Error:', error));
}

function startPartitioning() {
    const file = document.getElementById('uploadedFiles').value;
    const columns = Array.from(document.querySelectorAll('input[name="columns"]:checked')).map(el => el.value);
    let numGroups = document.getElementById('numGroups').value.trim();
    console.log("количество групп: ", numGroups);

    if (numGroups === "") {
      document.getElementById('log').innerText = ("Для начала работы введите необходимое количество итоговых групп")
      return;
    }
    if (!(/^\d+$/.test(numGroups))) {
      document.getElementById('log').innerText = "Необходимо ввести целое число для количества групп.";
      return;
    }
    numGroups = parseInt(numGroups);
    
    const bb = JSON.stringify({ file, numGroups, columns});
    console.log("json: ", bb);

    fetch('/partition', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: bb
    })
    .then(response => response.json())
    .then(data => {
        console.log(numGroups);
        document.getElementById('log').innerText = data.log || data.message;
    })
    .catch(error => {
        document.getElementById('log').innerText = "Error: " + error;
        console.error('Error:', error);
    });
}

function refreshFiles() {
    console.log("Refreshing files...");
    fetchUploadedFiles(); // Call function to load files
}

// Initial load of uploaded files when page loads
window.onload = refreshFiles;
