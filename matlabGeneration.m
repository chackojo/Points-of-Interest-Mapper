% Read and prepare the data
data = readtable('dataAA.csv');
lats = data.lat;
lons = data.lon;
weights = data.weight;

% Define the address location (16997 Boulder Dr, Northville, MI)
address_lat = 42.2808;  % Approximate latitude
address_lon = -83.7430; % Approximate longitude

% Create a grid for interpolation
gridSize = 100;  % Number of points in each dimension
latEdges = linspace(min(lats) - 0.001, max(lats) + 0.001, gridSize);
lonEdges = linspace(min(lons) - 0.001, max(lons) + 0.001, gridSize);
[LON, LAT] = meshgrid(lonEdges, latEdges);

% Initialize interpolated weight grid
weightGrid = zeros(size(LAT));

% Inverse Distance Weighting interpolation
p = 2;  % Power parameter (adjust for different smoothing effects)
for i = 1:size(LAT, 1)
    for j = 1:size(LAT, 2)
        % Calculate distances to all known points
        distances = sqrt((LAT(i,j) - lats).^2 + (LON(i,j) - lons).^2);
        
        % Avoid division by zero at known points
        distances(distances < 1e-10) = 1e-10;
        
        % Calculate weights using inverse distance
        weights_idw = 1 ./ (distances.^p);
        weights_idw = weights_idw / sum(weights_idw);
        
        % Calculate interpolated value
        weightGrid(i,j) = sum(weights .* weights_idw);
    end
end

% Create the visualization
figure('Position', [100, 100, 1200, 800]);

% Plot 1: Surface plot with interpolated weights
subplot(2,2,1);
surf(LON, LAT, weightGrid);
hold on;
plot3(address_lon, address_lat, max(max(weightGrid)), 'rp', 'MarkerSize', 20, 'MarkerFaceColor', 'r');
colorbar;
title('Surface Plot of POI Weights');
xlabel('Longitude');
ylabel('Latitude');
zlabel('Weight');
colormap(jet);
shading interp;
legend('Weight Surface', 'Address Location', 'Location', 'northeast');

% Plot 2: 2D heatmap with POI locations
subplot(2,2,2);
pcolor(LON, LAT, weightGrid);
hold on;
scatter(lons, lats, 50, weights, 'filled', 'MarkerEdgeColor', 'k');
plot(address_lon, address_lat, 'rp', 'MarkerSize', 20, 'MarkerFaceColor', 'r');
colorbar;
title('POI Locations with Weight Heatmap');
xlabel('Longitude');
ylabel('Latitude');
colormap(jet);
shading interp;
legend('Weight Heatmap', 'POIs', 'Address Location', 'Location', 'northeast');

% Plot 3: Contour plot
subplot(2,2,3);
contourf(LON, LAT, weightGrid, 20);
hold on;
scatter(lons, lats, 50, weights, 'filled', 'MarkerEdgeColor', 'k');
plot(address_lon, address_lat, 'rp', 'MarkerSize', 20, 'MarkerFaceColor', 'r');
colorbar;
title('Contour Plot of POI Weights');
xlabel('Longitude');
ylabel('Latitude');
legend('Weight Contours', 'POIs', 'Address Location', 'Location', 'northeast');

% Plot 4: 3D view with scatter points
subplot(2,2,4);
surf(LON, LAT, weightGrid, 'FaceAlpha', 0.7);
hold on;
scatter3(lons, lats, weights, 100, weights, 'filled', 'MarkerEdgeColor', 'k');
plot3(address_lon, address_lat, max(max(weightGrid)), 'rp', 'MarkerSize', 20, 'MarkerFaceColor', 'r');
colorbar;
title('3D Surface with POI Locations');
xlabel('Longitude');
ylabel('Latitude');
zlabel('Weight');
colormap(jet);
shading interp;
view(45, 30);
legend('Weight Surface', 'POIs', 'Address Location', 'Location', 'northeast');

% Adjust overall figure appearance
sgtitle('POI Weight Distribution Analysis - 16997 Boulder Dr, Northville MI');
set(gcf, 'Color', 'white');

% Add customization options
grid on;
box on;

% Optional: Save the figure
% saveas(gcf, 'poi_visualization.png');