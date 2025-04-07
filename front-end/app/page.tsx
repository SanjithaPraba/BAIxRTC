import { Pencil } from "lucide-react"
import "./styles.css"
import { useState } from "react"
import { Update } from "next/dist/build/swc/types";

export default function SlackbotSettings() {

  // State for form inputs 
  const [formData, setFormData] = useState({
    jsonExport: null,
    autoUpload: false,
    deleteFrom: "",
    deleteTo: "",
  });

  // Handle form submission to Flask
  const handleSubmit = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();

    const formDataToSend = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      if (value instanceof File) {
        formDataToSend.append(key, value);
      } else {
        formDataToSend.append(key, value);
      }
    });
  
  try {
    const response = await fetch("/your-flask-endpoint", {
      method: "POST",
      body: formDataToSend,
    });
    if (response.ok) {
      alert("Changes submitted successfully!");
    } else {
      alert("Error submitting changes!");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Error submitting changes!");
  }
};

  return (
    <div className="container">
      <div className="content">
        <h1 className="title">Member Support Slackbot Settings</h1>
        <div className="divider"></div>

        {/* Current Data State Section */}
        <DatabaseState/>
        <div className="divider"></div>

        {/* Update Data Section */}
        {/* formData is populated by UpdateDatabase component */}
        <UpdateDatabase formData={formData} setFormData={setFormData}/>
        <div className="divider"></div>

        {/* Update Task Escalation Section */}
        <StaffInformation/>

        <div className="submit-container">
          <button className="button button-primary">SUBMIT CHANGES</button>
        </div>

      </div>
    </div>
  )
}

{/* Current Data State Section */}
function DatabaseState() {
  return(
  <div>
    {/* get information via get request to flask  */}
    <section className="section">
      <h2 className="section-title">Current Data State</h2>

      <div className="card-grid">
        <div className="card">
          <p className="card-title">Last Upload</p>
          <p className="card-value">XX/XX/XX</p>
        </div>

        <div className="card">
            <p className="card-title">Stored Messages From</p>
            <p className="card-value">XX/XX/XX - XX/XX/XX</p>
        </div>

        <div className="card">
          <p className="card-title">AWS Storage Usage</p>
          <p className="card-value">XX MB / XX MB</p>
        </div>

        <div className="card">
          <p className="card-title">ChromaDB Storage Usage</p>
          <p className="card-value">XX MB / XX MB</p>
        </div>
      </div>
    </section>  
  </div>
  );
}

interface UpdateDatabaseProps {
  formData: { jsonExport: File | null; autoUpload: boolean; deleteFrom: string; deleteTo: string };
  setFormData: React.Dispatch<React.SetStateAction<any>>; // The type of setFormData is the dispatch function from useState
}

function UpdateDatabase({formData, setFormData} : UpdateDatabaseProps) {

  // Handle file change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, files } = e.target;

    if (files && files[0]) {
      setFormData((prevState: FormData) => ({
        ...prevState,
        [name]: files[0],
      }));
    }
  };

  // Handle checkbox change
  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData((prevState: FormData) => ({
      ...prevState,
      [name]: checked,
    }));
  };

  // Handle input change for text and date inputs
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevState: FormData) => ({
      ...prevState,
      [name]: value,
    }));
  };

  return(
  <div>
    <section className="section">
      <h2 className="section-title">Update Data</h2>
      <div className="update-data-container">

        <div className="update-data-column">
          <p className="item-title">Manually upload JSON exports</p>
          <input type="file" multiple name="jsonExport" onChange={handleFileChange}/>

          <div className="toggle-container">
            <div className="toggle-header">
              <p className="item-title">Automatically upload messages real-time</p>
              <label className="toggle">
                {/* for toggle to be accurate state, formData needs to be populated in parent component*/}
                <input type="checkbox" name="autoUpload" checked={formData.autoUpload} onChange={handleCheckboxChange}/>
                <span className="toggle-slider"></span>
              </label>
            </div>
            <p className="toggle-description">When disabled, all updates happen after a manual upload</p>
          </div>
        </div>

        <div className="update-data-column">
          <p className="item-title">Delete Data</p>

          <div className="date-inputs">
            <div className="date-input-group">
              <p className="date-label">From:</p>
              <input type="date" className="date-input" name="deleteFrom" onChange={handleInputChange} placeholder="mm/dd/yyyy" />
            </div>
            <div className="date-input-group">
              <p className="date-label">To:</p>
              <input type="date" className="date-input" name="deleteTo" onChange={handleInputChange} placeholder="mm/dd/yyyy" />
            </div>
          </div>
        </div>

      </div>
    </section>
  </div>
  );
}

function StaffInformation() {

  const allowEdits = (e: React.ChangeEvent<HTMLInputElement>) => {
    {/* allow user to edit staff info, divs turn into input boxes */}
  }
  return(
  <div>
    {/* Update Task Escalation Section */}
    <section className="section">
        <h2 className="section-title">Update Task Escalation</h2>

        <button className="button button-edit">
          Edit Staff Information <Pencil size={16} className="pencil-icon" />
        </button>

        <div className="staff-info">
          <p className="staff-name">Jane Doe</p>
          <input autoFocus type="text"/>
          <p className="staff-tasks">Tasks: Member Support, Scholarships</p>
        </div>
    </section>
  </div>
  );
}
