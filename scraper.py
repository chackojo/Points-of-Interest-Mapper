# -*- coding: utf-8 -*-
"""Scraper.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PCqG9cXwosnCVSvy-VgWltQo3Ttw-9hW
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import requests
import time

def get_location_dimensions(location_name):
    geolocator = Nominatim(user_agent="location_grid_colab_2024")
    try:
        location = geolocator.geocode(location_name)
        if not location:
            raise ValueError("Could not find the location.")

        bbox = location.raw['boundingbox']
        lat_diff = float(bbox[1]) - float(bbox[0])
        lon_diff = float(bbox[3]) - float(bbox[2])
        width = lon_diff * 111320  # Convert longitude degrees to meters
        height = lat_diff * 110574  # Convert latitude degrees to meters
        return width, height, location.latitude, location.longitude
    except Exception as e:
        print(f"Error getting location dimensions: {e}")
        raise

def get_pois(location_name, lat, lon):
    api_key = ""  # Replace with your API key
    radius = 9500  # 2 km radius

    # Define POI types with their base weights
    poi_type_weights = {
        "shopping_mall": 1.0,
        "tourist_attraction": 0.9,
        "restaurant": 0.8,
        "park": 0.7,
        "museum": 0.7,
        "university": 0.6,
        "library": 0.5,
        "store": 0.4,
        "church": 0.4,
        "business": 0.3,
        "stadium": 4,
        "arena": 8,
        "hospital": 1.0,
        "field": 0.7
    }

    pois = []

    for place_type, base_weight in poi_type_weights.items():
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius={radius}&type={place_type}&key={api_key}"
            response = requests.get(url, timeout=10).json()

            if 'results' in response:
                for place in response['results']:
                    # Calculate POI weight based on multiple factors
                    weight = base_weight

                    # Adjust weight based on rating if available
                    if 'rating' in place:
                        weight *= (place['rating'] / 5.0)

                    # Adjust weight based on user_ratings_total if available
                    if 'user_ratings_total' in place:
                        ratings_factor = min(place['user_ratings_total'] / 100, 2.0)  # Cap at 2x
                        weight *= ratings_factor

                    # Adjust weight based on price_level if available
                    if 'price_level' in place:
                        price_factor = (place['price_level'] + 1) / 4  # Normalize to 0.25-1
                        weight *= price_factor

                    pois.append({
                        'name': place.get('name'),
                        'lat': place['geometry']['location']['lat'],
                        'lon': place['geometry']['location']['lng'],
                        'type': place_type,
                        'weight': weight,
                        'rating': place.get('rating', 0),
                        'user_ratings': place.get('user_ratings_total', 0)
                    })

            time.sleep(0.5)  # Small delay between requests

        except Exception as e:
            print(f"Error fetching {place_type} POIs: {e}")
            continue

    return pois

def create_grid(width, height, scale, pois):
    if not pois:
        raise ValueError("No POIs available to create grid")

    grid_width = max(1, int(width / scale))
    grid_height = max(1, int(height / scale))
    grid = np.zeros((grid_height, grid_width))

    try:
        base_lon = min(poi['lon'] for poi in pois)
        base_lat = min(poi['lat'] for poi in pois)

        # Create a gaussian kernel for smooth weight distribution
        kernel_size = 5
        kernel = np.zeros((kernel_size, kernel_size))
        center = kernel_size // 2
        for i in range(kernel_size):
            for j in range(kernel_size):
                dist = np.sqrt((i - center)**2 + (j - center)**2)
                kernel[i, j] = np.exp(-dist)
        kernel = kernel / kernel.sum()

        for poi in pois:
            x = int((poi['lon'] - base_lon) * 111320 / scale)
            y = int((poi['lat'] - base_lat) * 110574 / scale)

            if 0 <= x < grid_width and 0 <= y < grid_height:
                # Apply weighted gaussian distribution around POI
                x_start = max(0, x - center)
                x_end = min(grid_width, x + center + 1)
                y_start = max(0, y - center)
                y_end = min(grid_height, y + center + 1)

                k_x_start = max(0, center - x)
                k_x_end = kernel_size - max(0, x + center + 1 - grid_width)
                k_y_start = max(0, center - y)
                k_y_end = kernel_size - max(0, y + center + 1 - grid_height)

                grid[y_start:y_end, x_start:x_end] += (
                    poi['weight'] * kernel[k_y_start:k_y_end, k_x_start:k_x_end]
                )

    except Exception as e:
        print(f"Error creating grid: {e}")
        raise

    return grid

def main():
    try:
        location_name = input("Enter the name of the location: ")
        width, height, lat, lon = get_location_dimensions(location_name)

        print("Fetching POIs...")
        pois = get_pois(location_name, lat, lon)

        if not pois:
            print("No POIs found. Please try a different location or larger radius.")
            return

        print(f"Found {len(pois)} POIs. Creating visualization...")

        # Create and display the grid
        grid = create_grid(width, height, 100, pois)

        plt.figure(figsize=(12, 10))
        plt.imshow(grid, cmap='viridis', interpolation='nearest')
        plt.colorbar(label='Interest Score')
        plt.title(f'Location Interest Heat Map: {location_name}')
        plt.xlabel('Longitude Grid')
        plt.ylabel('Latitude Grid')
        plt.show()

        # Save results
        df = pd.DataFrame(pois)
        output_file = f'{location_name.replace(" ", "_").lower()}_pois.csv'
        df.to_csv(output_file, index=False)
        print(f"Results saved to '{output_file}'")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
