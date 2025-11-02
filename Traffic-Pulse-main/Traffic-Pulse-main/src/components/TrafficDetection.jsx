import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, Camera, Loader2 } from 'lucide-react';

const TrafficDetection = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
    }
  };

  const handleDetection = async () => {
    if (!selectedFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:8000/detect', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Detection failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="w-5 h-5" />
          Traffic Detection
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload">
            <Button variant="outline" className="cursor-pointer">
              <Upload className="w-4 h-4 mr-2" />
              Select Image
            </Button>
          </label>
          
          <Button 
            onClick={handleDetection} 
            disabled={!selectedFile || loading}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Camera className="w-4 h-4 mr-2" />
            )}
            Detect Vehicles
          </Button>
        </div>

        {selectedFile && (
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2">Original Image</h3>
              <img 
                src={URL.createObjectURL(selectedFile)} 
                alt="Original" 
                className="w-full rounded-lg border"
              />
            </div>
            
            {result && (
              <div>
                <h3 className="font-medium mb-2">
                  Detection Result ({result.vehicle_count} vehicles)
                </h3>
                <img 
                  src={result.processed_image} 
                  alt="Processed" 
                  className="w-full rounded-lg border"
                />
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TrafficDetection;