import {
    TextField,
    DatagridConfigurable,
    Identifier,
    useTranslate,
} from 'react-admin';

export interface UserListDesktopProps {
    selectedRow?: Identifier;
}

const UserRow = ({ selectedRow }: UserListDesktopProps) => {
    const translate = useTranslate();

    return (
        <DatagridConfigurable
            bulkActionButtons={false}>
            <TextField source="id" label={translate('resources.users.fields.id')} sortable={true} />
            <TextField source="username" label={translate('resources.users.fields.username')} sortable={false} />
            <TextField source="email" label={translate('resources.users.fields.email')} sortable={false} />
            <TextField source="nickname" label={translate('resources.users.fields.nickname')} sortable={false} />
        </DatagridConfigurable>
    );
};

export default UserRow;