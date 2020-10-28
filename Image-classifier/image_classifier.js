// MobileNet model
var net;

// Function loads MobileNet model
async function loadModel() {
    console.log('Loading mobilenet.');
    net = await mobilenet.load();
    document.getElementById('label').innerHTML = 'Model loaded.';
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

// Function changes the image on HTTP page
function newImage(url) {
    document.getElementById('img').src = url
}

// Function prompts user to enter new url
function urlEntry() {
    console.log('Should show entry window...');
    let newUrl;
    newUrl = prompt('Enter an image url:', '');
    if (newUrl != null) {
        newImage(newUrl)
    }
}

// On clicking the button we prompt user to enter new url
document.getElementById('entry').addEventListener('click', urlEntry)

// On clicking the button we display image label
document.getElementById('classify').addEventListener('click', getLabel)
