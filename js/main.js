let currentCarCode = ''; // Store the code of the car being edited

async function loadCars() {
    try {
        const response = await fetch('/car_register.php');
        if (!response.ok) {
            throw new Error('Failed to fetch cars');
        }

        const data = await response.json();

        if (data.status === 200 && data.data) {
            const cars = data.data;
            const tbody = document.querySelector('tbody');
            tbody.innerHTML = '';  

            cars.forEach(car => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${car.code}</td>
                    <td>${car.owner}</td>
                    <td>${car.brand}</td>
                    <td>${car.license_plate}</td>
                    <td>${car.color}</td>
                    <td>
                        <a id="js-modal-confirm" class="uk-button uk-button-default" href="#" uk-toggle="target: #edit-modal" onclick="openEditModal('${car.code}', '${car.owner}', '${car.brand}', '${car.license_plate}', '${car.color}')">edit</a>
                        <a href="car_register.php?brand=${car.brand}&license_plate=${car.license_plate}" target="_blank" class="uk-button uk-button-default">data set</a>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading cars:', error);
    }
}

function openEditModal(code, owner, brand, licensePlate, color) {
    currentCarCode = code; 
    document.getElementById("editCode").value = code;
    document.getElementById("editOwner").value = owner;
    document.getElementById("editBrand").value = brand;
    document.getElementById("editLicensePlate").value = licensePlate;
    document.getElementById("editColor").value = color;
}

async function updateCar(event) {
    event.preventDefault();

    var code = document.getElementById("editCode").value;
    var owner = document.getElementById("editOwner").value;
    var brand = document.getElementById("editBrand").value;
    var license_plate = document.getElementById("editLicensePlate").value;
    var color = document.getElementById("editColor").value;

    const carData = {
        owner: owner,
        brand: brand,
        license_plate: license_plate,
        color: color
    };

    try {
        const response = await fetch(`/car_register.php?code=${code}`, {
            method: 'PUT', 
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(carData)
        });

        const data = await response.json();

        if (!response.ok) {
            showAlert("Invalid input data");
            return; 
        }

        UIkit.modal('#edit-modal').hide();
        loadCars(); 

    } catch (error) {
        console.error('Error updating car:', error);
        showAlert('An unexpected error occurred. Please try again later.', '#edit-modal');
    }
}

async function addCar(event) {
    event.preventDefault();

    var owner = document.getElementById("addOwner").value;
    var brand = document.getElementById("addBrand").value;
    var licensePlate = document.getElementById("addLicensePlate").value;
    var color = document.getElementById("addColor").value;


    const carData = {
        code: 0,
        owner: owner,
        brand: brand,
        license_plate: licensePlate,
        color: color
};

try {
const response = await fetch('/car_register.php', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(carData)
});

const data = await response.json();

if (!response.ok) {
    showAlert(data.message, '#add-car-modal');
    return;
}

document.querySelector('#add-car-modal form').reset();
loadCars();

UIkit.modal('#add-car-modal').hide();

} catch (error) {
console.error('Error adding car:', error);
showAlert('An unexpected error occurred. Please try again later.', '#add-car-modal');
}
}

function showAlert(message, modalId) {
const alertContainer = document.querySelector(`${modalId} .modal-alert-container`);
alertContainer.innerHTML = `
<div class="uk-alert-danger" uk-alert>
    <a class="uk-alert-close" uk-close></a>
    <p>${message}</p>
</div>
`;
alertContainer.style.display = 'block';
}


window.addEventListener('DOMContentLoaded', () => {
    loadCars();
    document.querySelector('#add-car-modal button.uk-button-default').addEventListener('click', addCar);
    document.querySelector('#edit-modal button.uk-button-default').addEventListener('click', updateCar);
});