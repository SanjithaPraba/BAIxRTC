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

  // useEffect(() => {
  //   const fetchInfo = async () => {
  //     try {
  //       const response = await fetch("http://localhost:5000/api/db");
  //       if (response.ok) {
  //         const data = await response.json();
  //         setInfo(data);
  //       } else {
  //         console.error("Error fetching data");
  //       }
  //     } catch (error) {
  //       console.error("Error:", error);
  //     }
  //   };

  //   fetchInfo();
  // }, []); // should only run once during component mount

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
        const response = await fetch("http:localhost:5000/api/db", {
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
            <p className="description">When disabled, all updates happen after a manual upload</p>
          </div>

          <div className="submit-container">
          <button className="button button-primary" onSubmit={handleSubmit}>SUBMIT CHANGES</button>
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

interface StaffMember {
  name: string;
  tasks: string;
  accountId: string;
}

function StaffInformation() {


  const [isEditing, setIsEditing] = useState(false);
  const [staffList, setStaffList] = useState<StaffMember[]>([]);

  useEffect(() => { // initial get + display staff list
    const fetchStaffList = async () => {
      try {
        const response = await fetch("http://localhost:5000/api/staff")
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

  // updates specific field for staff member
  // index for member, field for what to update, value
  const handleInputChange = (index: number, field: "name" | "tasks" | "accountId", value:string) => {
    setStaffList((prev) =>
      //loop through previous state of staff list
      prev.map((staff, i) =>
        //new object, copy prev data, update with new value
        i === index ? {...staff, [field]: value } : staff 
      )
    );
  };

  const addNewStaff = () => {
    setStaffList((prev) => [...prev, {name: "", tasks: "", accountId: ""}]);
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/staff", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(staffList),
      });

      if (!response.ok) throw new Error("Failed to save staff list");
      alert("Staff list saved!");
    } catch (err) {
      console.error("Error saving:", err);
    }
  };

  return (
    <div>
      {/* Update Task Escalation Section */}
      <section className="section">
      <h2 className="section-title">Update Task Escalation</h2>

      <button className="button button-edit" onClick={handleEdit}>
        {isEditing ? "Done Editing" : "Edit Staff Information"}{" "}
        <Pencil size={16} className="pencil-icon" />
      </button>
      <p className="task-description">
        {isEditing? "Write task categories separated by comma (ex. Scholarships, Account Recovery, .." : ""}
      </p>

      <div className="staff-info">
        {staffList.map((staff, index) => (
          <div key={index} className="staff-entry">
            {isEditing ? (
              <div>
                  <div className="staff-item">
                    <p className="staff-field">Name: </p>
                    <input className="staff-name" type="text" value={staff.name}
                    onChange={(e) => handleInputChange(index, "name", e.target.value)}
                    placeholder={staff.name}/>
                  </div>
                  <div className="staff-item"> 
                    <p className="staff-field">Account: </p>
                    <input className="staff-account" type="text" value={staff.accountId}
                    onChange={(e) => handleInputChange(index, "accountId", e.target.value)}
                    placeholder={staff.accountId}/>
                  </div>
                  <div className="staff-item">
                    <p className="staff-field">Tasks: </p>
                    <input className="staff-tasks" type="text" value={staff.tasks}
                    onChange={(e) => handleInputChange(index, "tasks", e.target.value)}
                    placeholder={staff.tasks}/>
                  </div>
                  <div className="divider"></div>
              </div>
            ) : (
              <div>
                <div className="staff-item">
                  <p className="staff-field">Name: </p>
                  <p className="staff-name">{staff.name}</p>
                </div>
                <div className="staff-item">
                  <p className="staff-field">Account: </p>
                  <p className="staff-account">{staff.accountId}</p>
                </div>
                <div className="staff-item">
                  <p className="staff-field">Tasks: </p>
                  <p className="staff-tasks">{staff.tasks}</p>
                </div>
                <div className="divider"></div>
              </div>
            )}
          </div>
        ))}

        {isEditing && (
          <button className="button button-edit" onClick={addNewStaff}>
            + Add Staff Member
          </button>
        )}        
      </div>

        <div className="submit-container">
          <button className="button button-primary" onClick={handleSubmit}>
            SUBMIT CHANGES
          </button>
        </div>
      </section>
    </div>
  );
}
