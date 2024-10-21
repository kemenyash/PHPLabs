<?php

header("Content-Type: application/json; charset=UTF-8");
$method = $_SERVER['REQUEST_METHOD'];
$dataSetFilename = 'dataset.json';


$cars = getDataSet(); // Отримуємо всі автомобілі з файлу в асоціативному масиві

switch ($method) {
    case 'GET': // Отримуємо інформацію про автомобілі чи dataset по конкретному
        if (isset($_GET['license_plate']) && isset($_GET['brand'])) { // Отриманя інфо по конкретному автомобілю з допомогою GET (приклад: /car_register.php?brand=Chrysler&license_plate=AO9876DD)
            $brand = $_GET['brand'];
            $licensePlate = $_GET['license_plate'];
            $car = getCar($cars, $brand, $licensePlate);

            if (count($car) > 0) {
                http_response_code(200);
                echo json_encode([
                    "status" => 200,
                    "data" => array_values($car)
                ]);
            } else {
                http_response_code(404);
                echo json_encode([
                    "status" => 404,
                    "message" => "Car not found"
                ]);
            }
        } else { // Якщо GET без параметрів - віддаємо все, що є
            http_response_code(200);
            echo json_encode([
                "status" => 200,
                "data" => $cars
            ]);
        }
        break;

    case 'POST': // Додаємо новий автомобіль
        $input = json_decode(file_get_contents("php://input"), true);

        $input['code'] = count($cars) + 1;
        if (validateInput($input)) {
            foreach ($cars as $car) {
                if ($car['license_plate'] == $input['license_plate']) {
                    http_response_code(400);
                    echo json_encode([
                        "status" => 400,
                        "message" => "Car with this license plate already exists"
                    ]);
                    exit;
                }
            }
            
            $cars[] = $input; // Корегуємо загальний список машин
            updateDataSet($cars); // Апдейтим датасет

            http_response_code(201);
            echo json_encode([
                "status" => 201,
                "message" => "Car added successfully"
            ]);
        } else {
            http_response_code(400);
            echo json_encode([
                "status" => 400,
                "message" => "Invalid input data"
            ]);
        }
        break;

    case 'PUT': // Оновлюємо дані автомобіля за його кодом
        if (isset($_GET['code'])) {
            $code = $_GET['code'];
            $input = json_decode(file_get_contents("php://input"), true);

            if (!validateInput($input)) {
                http_response_code(400);
                echo json_encode([
                    "status" => 400,
                    "message" => "Invalid input data"
                ]);
                exit;
            }

            $found = false;
            foreach ($cars as &$car) {
                if ($car['code'] == $code) {
                    $car = array_merge($car, $input); // Оновлюємо дані автомобіля
                    $found = true;
                    break;
                }
            }

            if ($found) {
                updateDataSet($cars);
                http_response_code(200);
                echo json_encode([
                    "status" => 200,
                    "message" => "Car updated successfully"
                ]);
            } else {
                http_response_code(404);
                echo json_encode([
                    "status" => 404,
                    "message" => "Car not found"
                ]);
            }
        } else {
            http_response_code(400);
            echo json_encode([
                "status" => 400,
                "message" => "License plate is required"
            ]);
        }
        break;

    default:
        http_response_code(400);
        echo json_encode([
            "status" => 400,
            "message" => "Bad request"
        ]);
        break;
}

#region Functions

function validateInput($input) {
    $brandRegex = '/^[A-Za-z0-9 ]{1,40}$/'; // Латинські букви, цифри, пробіли, до 40 символів
    $licensePlateRegex = '/^[A-Za-z0-9]{1,8}$/'; // Латинські букви, цифри, до 8 символів, без пробілів
    $colorRegex = '/^[A-Za-z ]{1,40}$/'; // Латинські букви, пробіли, до 40 символів
    $ownerRegex = '/^[A-Za-z ]{1,40}$/'; // Латинські букви, пробіли, до 40 символів

    return isset($input['brand'], $input['license_plate'], $input['owner'], $input['color'])
        && preg_match($brandRegex, $input['brand'])
        && preg_match($licensePlateRegex, $input['license_plate'])
        && preg_match($colorRegex, $input['color'])
        && preg_match($ownerRegex, $input['owner']);
}


function getDataSet() {
    $jsonData = file_get_contents('dataset.json'); // Витягуємо дані з файлу dataset.json
    return json_decode($jsonData, true);
}

function getCar($cars, $brand, $licensePlate) {
    $result = []; 
    foreach ($cars as $car) {
        if ($car['brand'] == $brand && $car['license_plate'] == $licensePlate) { // Перебираємо масив, щоб знайти потрібну машину
            $result[] = $car;
        }
    }
    return $result;
}

function updateDataSet($cars) {
    file_put_contents('dataset.json', json_encode($cars, JSON_PRETTY_PRINT)); // Вставляємо дані з заміною в Dataset.json
}

#endregion

?>
