// MobileNet model
var net;

// Function loads MobileNet model
async function loadModel() {
    console.log('Loading MobileNet.');
    net = await mobilenet.load();
    document.getElementById('label').innerHTML = 'Модель загружена.';
    console.log('Successfully loaded model.');
}

loadModel()

// Function classifies the image
async function getLabel() {
  // Reference to 'img' element on HTTP page
  const imgEl = document.getElementById('img');
    // Classify the image
    const result = await net.classify(imgEl);
    console.log(result);
    // Percent probability (rounded)
    let probability = (result[0].probability * 100).toFixed(2)
    // Display the label below the image
    document.getElementById('label').innerHTML = `${result[0].className}: ${probability}%`;
}

// For uploading image from the file slelected by user
var uploadImageFile = function(event) {
    var output = document.getElementById('img');
    output.src = URL.createObjectURL(event.target.files[0]);
    output.onload = function() {
      URL.revokeObjectURL(output.src) // free memory
    }
  }

// On clicking the button we display image label
document.getElementById('classify').addEventListener('click', getLabel)
