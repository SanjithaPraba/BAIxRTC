"use client";
import { Pencil } from "lucide-react"
import "./styles.css"
import { useState, useEffect } from "react"
import { Update } from "next/dist/build/swc/types";

export default function SlackbotSettings() {
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
        <UpdateDatabase/>
        <div className="divider"></div>

        {/* Update Task Escalation Section */}
        <StaffInformation/>

      </div>
    </div>
  )
}

{/* Current Data State Section */}
function DatabaseState() {

  // state for db
  const [info, setInfo] = useState({
    lastUpload: "XX/XX/XX",
    dateRange: "XX/XX/XX - XX/XX/XX",
    awsUsage: "XX / XX MB",
    chromaUsage: "XX / XX MB",
  });

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const response = await fetch("https://localhost:5000/api/db");
        if (response.ok) {
          const data = await response.json();
          setInfo(data);
        } else {
          console.error("Error fetching data");
        }
      } catch (error) {
        console.error("Error:", error);
      }
    };

    fetchInfo();
  }, []); // should only run once during component mount

  return(
  <div>
    {/* get information via get request to flask  */}
    <section className="section">
      <h2 className="section-title">Current Data State</h2>

      <div className="card-grid">
        <div className="card">
          <p className="card-title">Last Upload</p>
          <p className="card-value">{info.lastUpload}</p>
        </div>

        <div className="card">
            <p className="card-title">Stored Messages From</p>
            <p className="card-value">{info.dateRange}</p>
        </div>

        <div className="card">
          <p className="card-title">AWS Storage Usage</p>
          <p className="card-value">{info.awsUsage}</p>
        </div>

        <div className="card">
          <p className="card-title">ChromaDB Storage Usage</p>
          <p className="card-value">{info.chromaUsage}</p>
        </div>
      </div>
    </section>  
  </div>
  );
}

function UpdateDatabase() {

    // State for form inputs 
    const [formData, setFormData] = useState({
      jsonExport: null,
      autoUpload: false,
      deleteFrom: "",
      deleteTo: "",
    });
  
    // Handle form submission to Flask
    const handleSubmit = async (e: React.FormEvent<HTMLButtonElement>) => {
      e.preventDefault(); //stops form from instantly submitting
      const formDataToSend = new FormData();
      Object.entries(formData).forEach(([key, value]) => {
        if (typeof value === "string") {
          formDataToSend.append(key, value as string);
        }
        else if (typeof value === "boolean") {
          formDataToSend.append(key, String(value));
        } else if (key === "jsonExport" && value !== null && (value as any) instanceof Blob) {
          formDataToSend.append(key, value as Blob);
        } 
      });
    
      try {
        const response = await fetch("https:localhost:5000/api/db", {
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

  // Handle file change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, files } = e.target;

    if (files && files[0]) {
      setFormData((prevState) => ({
        ...prevState,
        [name]: files[0],
      }));
    }
  };

  // Handle checkbox change
  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: checked,
    }));
  };

  // Handle input change for text and date inputs
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevState) => ({
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
        
        <div className="submit-container">
          <button className="button button-primary" onSubmit={handleSubmit}>SUBMIT CHANGES</button>
        </div>
      </div>

    </section>
  </div>
  );
}

function StaffInformation() {

  const [isEditing, setIsEditing] = useState(false);
  const [staffList, setStaffList] = useState<{ name: string; tasks: string[] }[]>([]);

  useEffect(() => { // initial get + display staff list
    const fetchStaffList = async () => {
      try {
        const response = await fetch("https://localhost:5000/api/staff")
        if (response.ok) {
          const data = await response.json();
          setStaffList(data);
        }
      } catch {
        console.error("Error fetching staff list");
      }
    }

    fetchStaffList();
  }, []);

  const handleEdit = () => { // toggles edit mode
    setIsEditing(!isEditing);
  }

  // const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>, index: number, field: string ) => {
  //   const updatedStaff = [... staffList];
  //   updatedStaff[index]: {
  //     ...updatedStaff[index],
  //     [field]: e.target.value
  //   };
  //   setStaffList(updatedStaff);
  // }

  const handleSubmit = async (e: React.FormEvent<HTMLButtonElement>) => {
    e.preventDefault(); //stops form from instantly submitting
    const formDataToSend = new FormData();
    Object.entries(staffList).forEach(([key, value]) => {
      if (typeof value === "string") {
        formDataToSend.append(key, value as string);
      }
    });
  
    try {
      const response = await fetch("https:localhost:5000/api/staff", {
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

  return(
  <div>
    {/* Update Task Escalation Section */}
    <section className="section">
        <h2 className="section-title">Update Task Escalation</h2>

        <button className="button button-edit" onClick={handleEdit}>
          {isEditing ? "Edit Staff Information" : "Save Staff Information"} <Pencil size={16} className="pencil-icon" />
        </button>

        <div className="staff-info">
        {isEditing ? 
          <div>
            <input className="staff-name" autoFocus type="text"/>
            <input className="staff-tasks" autoFocus type="text"/>
          </div>
        :
          <div>
            <p className="staff-name">Jane Doe</p>
            <p className="staff-tasks">Tasks: Member Support, Scholarships</p>
          </div>
        }
        </div>

        <div className="submit-container">
          <button className="button button-primary" onSubmit={handleSubmit}>SUBMIT CHANGES</button>
        </div>

    </section>
  </div>
  );
}
