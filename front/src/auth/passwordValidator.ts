import { Validator } from 'react-admin';

/**
 * A react-admin validator that checks that a field matches another field.
 * @param field The name of the field to compare to.
 * @param message The message to display when the fields do not match. Defaults to 'ra.validation.do_not_match'.
 * @example
 * import { validatePasswordsMatch } from 'ra-auth-cognito';
 * import { SimpleForm, TextInput } from 'react-admin';
 *
 * const MyForm = () => (
 *    <SimpleForm>
 *       <TextInput source="password" type="password" />
 *      <TextInput source="passwordConfirm" type="password" validate={validatePasswordsMatch('password')} />
 *   </SimpleForm>
 * );
 */
export const validatePasswordsMatch =
    (
        field: string,
        message = {
            message: 'ra.validation.do_not_match',
            args: { _: 'Passwords do not match' },
        }
    ): Validator =>
    (value: string, allValues: any) => {
        if (value !== allValues[field]) {
            return message;
        }
    };

export const validatePasswordPolicy = (value: string): string | undefined => {
    if (!value) {
        return 'パスワードは必須です';
    }
    
    const requirements = [
        {
        test: value.length >= 8,
        message: '8文字以上である'
        },
        {
        test: /\d/.test(value),
        message: '数字を1つ以上含む'
        },
        {
        test: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value),
        message: '特殊文字を1つ以上含む (!@#$%^&*()_+-=[]{}|;\':"\\.,<>?/)'
        },
        {
        test: /[A-Z]/.test(value),
        message: '大文字を1つ以上含む'
        },
        {
        test: /[a-z]/.test(value),
        message: '小文字を1つ以上含む'
        }
    ];
    
    const failedRequirements = requirements
        .filter(req => !req.test)
        .map(req => req.message);
    
    return failedRequirements.length > 0
        ? `パスワードは以下の条件を満たす必要があります:\n• ${failedRequirements.join('\n• ')}`
        : undefined;
    };